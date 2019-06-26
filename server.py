import logging
import os
import requests

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest
from urllib3.exceptions import NewConnectionError

from prometheus_metrics import generate_aggregated_metrics
from workers import ai_service_worker, _retryable


def create_application():
    """Create Flask application instance."""
    app = Flask(__name__)
    app.config['AI_SERVICE'] = os.environ.get('AI_SERVICE')
    app.config['NEXT_SERVICE_URL'] = os.environ.get('NEXT_SERVICE_URL')
    app.config['IF_NUM_TREES_FACTOR'] = os.environ.get('IF_NUM_TREES_FACTOR')
    app.config['IF_SAMPLE_SIZE_FACTOR'] = \
        os.environ.get('IF_SAMPLE_SIZE_FACTOR')
    return app


APP = create_application()
APP.logger = logging.getLogger('server')

VERSION = "0.0.1"


@APP.route("/", methods=['GET'])
def get_root():
    """Root Endpoint for Liveness/Readiness check."""
    next_service = APP.config['NEXT_SERVICE_URL']
    try:
        _retryable('get', f'{next_service}')
        status = 'OK'
        message = 'Up and Running'
        status_code = 200
    except (requests.HTTPError, NewConnectionError):
        status = 'Error'
        message = 'aiops-publisher not operational'
        status_code = 500

    return jsonify(
        status=status,
        version=VERSION,
        message=message
    ), status_code


@APP.route("/", methods=['POST', 'PUT'])
def index():
    """Pass data to next endpoint."""
    next_service = APP.config['NEXT_SERVICE_URL']
    env = {
        'ai_service': APP.config['AI_SERVICE'],
        'num_trees_factor': APP.config['IF_NUM_TREES_FACTOR'],
        'sample_size_factor': APP.config['IF_SAMPLE_SIZE_FACTOR'],
    }

    try:
        input_data = request.get_json(force=True, cache=False)
    except BadRequest:
        return jsonify(
            status='ERROR',
            message="Unable to parse input data JSON.",
        ), 400

    b64_identity = request.headers.get('x-rh-identity')

    ai_service_worker(
        input_data,
        next_service,
        env,
        b64_identity,
    )

    APP.logger.info('Job started')

    return jsonify(
        status='OK',
        message='Outlier detection initiated.',
    )


@APP.route("/metrics", methods=['GET'])
def get_metrics():
    """Metrics Endpoint."""
    return generate_aggregated_metrics()


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8005))
    APP.run(port=PORT)
