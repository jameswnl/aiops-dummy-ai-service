import argparse
import json

from workers import ai_service_worker

def run(args):
    print('opening:', args.input_path)
    with open(args.input_path) as f:
        job = json.load(f)
    ai_service_worker(job, args.output_path)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  # arguments
  parser.add_argument(
      '--input_path', type=str, required=True, help='input path'
  )
  parser.add_argument(
      '--output_path', type=str, required=True, help='output path'
  )
  parser.add_argument(
      '--job_id', type=str, required=True, help='Job ID'
  )

  # Parse all arguments
  args = parser.parse_args()
  
run(args)
