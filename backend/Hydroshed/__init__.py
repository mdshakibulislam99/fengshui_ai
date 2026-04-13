# HydroSHEDS module for river network analysis 
# Now supports both GEE (legacy) and China's National River Network (native)

from .hydrosheds_service import HydroSHEDSService
from .china_river_service import ChinaRiverService

__all__ = ['HydroSHEDSService', 'ChinaRiverService']
