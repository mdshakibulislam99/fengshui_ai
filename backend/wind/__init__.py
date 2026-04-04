# Wind Data Service Module
# Provides ERA5 wind analysis from Google Earth Engine
# Integrated with Feng Shui analysis for wind flow and exposure scoring

from .era5_service import ERA5WindService

__all__ = ['ERA5WindService']
