import os
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from services.shapefile_service import ShapefileService

TEMP_DIR = "/tmp/shapes"

class ShapeAwsService(ShapefileService):
    """
    Same interface as ShapefileService but sources shapefiles from S3.

    Required env vars:
      AWS_S3_BUCKET        — S3 bucket name
      AWS_S3_PREFIX        — key prefix inside the bucket (default: shapes/chile)

    Standard boto3 credential chain applies:
      AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN
      AWS_DEFAULT_REGION
      IAM role (EC2 / ECS / Lambda)

    Expected S3 layout (mirrors local static/shapes/chile/):
      {prefix}/regiones/Regional.shp  (.shx .dbf .prj .cpg ...)
      {prefix}/regiones/regions.json
      {prefix}/provincias/Provincias.shp  (...)
      {prefix}/comunas/comunas.shp  (...)
    """

    _map_regs = None
    _map_prov = None
    _map_comn = None
    _regions = []
    _file_name_regs = None
    _file_name_prov = None
    _file_name_comn = None
    _initialized = False

    def _init_paths(self):
        temp_dir = self._download_from_s3()
        cls = type(self)
        cls._file_name_regs = os.path.join(temp_dir, 'regiones', 'Regional.shp')
        cls._file_name_prov = os.path.join(temp_dir, 'provincias', 'Provincias.shp')
        cls._file_name_comn = os.path.join(temp_dir, 'comunas', 'comunas.shp')
        self._json_regions_file = os.path.join(temp_dir, 'regiones', 'regions.json')

    def _download_from_s3(self) -> str:
        bucket = os.environ.get('AWS_S3_BUCKET')
        prefix = os.environ.get('AWS_S3_PREFIX', 'chile').rstrip('/')

        if not bucket:
            raise ValueError("AWS_S3_BUCKET environment variable is required")

        if not os.path.exists(TEMP_DIR):
            logging.info(f"[ShapeAwsService] Downloading shapefiles from s3://{bucket}/{prefix}")
            s3 = boto3.client('s3')
            os.makedirs(TEMP_DIR)
            temp_dir = TEMP_DIR
            try:
                paginator = s3.get_paginator('list_objects_v2')
                downloaded = 0

                for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    for obj in page.get('Contents', []):
                        key = obj['Key']
                        relative_path = key[len(prefix):].lstrip('/')
                        if not relative_path:
                            continue

                        local_path = os.path.join(temp_dir, relative_path)
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)

                        logging.info(f"[ShapeAwsService] Downloading: s3://{bucket}/{key}")
                        s3.download_file(bucket, key, local_path)
                        downloaded += 1

                if downloaded == 0:
                    raise FileNotFoundError(
                        f"No files found in s3://{bucket}/{prefix}. "
                        f"Check AWS_S3_BUCKET and AWS_S3_PREFIX."
                    )

                logging.info(f"[ShapeAwsService] {downloaded} files downloaded to {temp_dir}")
                return temp_dir

            except (BotoCoreError, ClientError) as e:
                logging.error(f"[ShapeAwsService] AWS error: {e}")
                raise
        logging.info(f"[ShapeAwsService] Using existing temporary directory: {TEMP_DIR}")
        return TEMP_DIR
