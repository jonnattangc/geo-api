import os
from abc import ABC, abstractmethod


class BaseShapefileService(ABC):
    """
    Abstract interface for shapefile-based geographic queries.

    Concrete implementations:
      ShapefileService  — reads shapefiles from local disk
      ShapeAwsService   — downloads shapefiles from S3, then queries them

    Factory
    -------
    Use BaseShapefileService.create() to get the appropriate implementation
    based on the USE_AWS_SHAPES environment variable:
      USE_AWS_SHAPES=true   -> ShapeAwsService
      USE_AWS_SHAPES=false  -> ShapefileService  (default)
    """

    @staticmethod
    def create() -> 'BaseShapefileService':
        use_aws = os.environ.get('USE_AWS_SHAPES', 'false').lower() == 'true'
        if use_aws:
            from services.shapeaws_service import ShapeAwsService
            return ShapeAwsService()
        from services.shapefile_service import ShapefileService
        return ShapefileService()

    @abstractmethod
    def get_list(self, shape: str, region: str) -> tuple:
        """Return a list of geographic elements and an HTTP status code."""

    @abstractmethod
    def region_name(self, id: str) -> str:
        """Return the display name of a region by its code."""

    @abstractmethod
    def get_zones(self, data_rx: dict) -> tuple:
        """Resolve search term, zone type, and GeoDataFrame from a zone dict."""

    @abstractmethod
    def get_zone_point(self, point, zones) -> object:
        """Return the GeoDataFrame rows that contain the given point."""

    @abstractmethod
    def inside_verification(self, area, search: str, shape: str) -> dict:
        """Check whether the found area matches the searched name."""
