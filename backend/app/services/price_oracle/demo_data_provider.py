"""Demo data provider for development and fallback"""
import random
from datetime import datetime
from typing import Dict, List, Optional

from .models import (
    CommodityPriceData,
    Location,
    PriceData,
    PriceSource,
)


class DemoDataProvider:
    """Provides realistic demo data for development and fallback"""
    
    def __init__(self):
        self.demo_data = self._load_demo_data()
        self.price_variation = 0.1  # 10% random variation
    
    def _load_demo_data(self) -> Dict[str, CommodityPriceData]:
        """
        Loads demo price data for 50+ common agricultural commodities
        Based on typical Indian agricultural market prices (in Rs per kg)
        """
        return {
            # Vegetables
            "tomato": CommodityPriceData(
                base_price=20.0,
                seasonal_factors={
                    1: 1.2, 2: 1.1, 3: 0.9, 4: 0.8, 5: 0.85, 6: 0.9,
                    7: 1.0, 8: 1.1, 9: 1.15, 10: 1.2, 11: 1.1, 12: 1.15
                },
                regional_variations={
                    "Maharashtra": 1.0,
                    "Karnataka": 0.95,
                    "Tamil Nadu": 1.05,
                    "Andhra Pradesh": 0.98,
                    "Telangana": 0.97,
                    "Gujarat": 1.02,
                    "Madhya Pradesh": 0.93,
                    "Rajasthan": 1.08,
                    "Uttar Pradesh": 0.96,
                    "West Bengal": 1.03,
                }
            ),
            "onion": CommodityPriceData(
                base_price=25.0,
                seasonal_factors={
                    1: 0.9, 2: 0.85, 3: 0.9, 4: 1.0, 5: 1.1, 6: 1.2,
                    7: 1.3, 8: 1.2, 9: 1.1, 10: 1.0, 11: 0.95, 12: 0.9
                },
                regional_variations={
                    "Maharashtra": 1.0,
                    "Karnataka": 0.92,
                    "Tamil Nadu": 1.08,
                    "Andhra Pradesh": 0.96,
                    "Telangana": 0.95,
                    "Gujarat": 1.05,
                    "Madhya Pradesh": 0.98,
                    "Rajasthan": 1.12,
                    "Uttar Pradesh": 0.94,
                    "West Bengal": 1.06,
                }
            ),
            "potato": CommodityPriceData(
                base_price=18.0,
                seasonal_factors={
                    1: 0.85, 2: 0.9, 3: 1.0, 4: 1.1, 5: 1.15, 6: 1.2,
                    7: 1.15, 8: 1.1, 9: 1.0, 10: 0.95, 11: 0.9, 12: 0.85
                },
                regional_variations={
                    "Maharashtra": 1.0,
                    "Karnataka": 0.97,
                    "Tamil Nadu": 1.03,
                    "Andhra Pradesh": 0.99,
                    "Telangana": 0.98,
                    "Gujarat": 1.01,
                    "Madhya Pradesh": 0.95,
                    "Rajasthan": 1.04,
                    "Uttar Pradesh": 0.92,
                    "West Bengal": 1.02,
                }
            ),
            "cabbage": CommodityPriceData(
                base_price=15.0,
                seasonal_factors={
                    1: 0.9, 2: 0.85, 3: 0.9, 4: 1.0, 5: 1.1, 6: 1.2,
                    7: 1.15, 8: 1.1, 9: 1.0, 10: 0.95, 11: 0.9, 12: 0.85
                },
                regional_variations={
                    "Maharashtra": 1.0,
                    "Karnataka": 0.96,
                    "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98,
                    "Telangana": 0.97,
                    "Gujarat": 1.02,
                    "Madhya Pradesh": 0.94,
                    "Rajasthan": 1.06,
                    "Uttar Pradesh": 0.95,
                    "West Bengal": 1.01,
                }
            ),
            "cauliflower": CommodityPriceData(
                base_price=22.0,
                seasonal_factors={
                    1: 0.8, 2: 0.85, 3: 0.95, 4: 1.1, 5: 1.2, 6: 1.3,
                    7: 1.25, 8: 1.15, 9: 1.05, 10: 0.95, 11: 0.85, 12: 0.8
                },
                regional_variations={
                    "Maharashtra": 1.0,
                    "Karnataka": 0.94,
                    "Tamil Nadu": 1.06,
                    "Andhra Pradesh": 0.97,
                    "Telangana": 0.96,
                    "Gujarat": 1.03,
                    "Madhya Pradesh": 0.93,
                    "Rajasthan": 1.08,
                    "Uttar Pradesh": 0.92,
                    "West Bengal": 1.04,
                }
            ),
            "carrot": CommodityPriceData(
                base_price=28.0,
                seasonal_factors={
                    1: 0.85, 2: 0.9, 3: 1.0, 4: 1.1, 5: 1.15, 6: 1.2,
                    7: 1.15, 8: 1.1, 9: 1.0, 10: 0.95, 11: 0.9, 12: 0.85
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.95, "Tamil Nadu": 1.05,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.94, "Rajasthan": 1.07, "Uttar Pradesh": 0.93,
                    "West Bengal": 1.02,
                }
            ),
            "brinjal": CommodityPriceData(
                base_price=24.0,
                seasonal_factors={
                    1: 1.1, 2: 1.05, 3: 0.95, 4: 0.9, 5: 0.9, 6: 0.95,
                    7: 1.0, 8: 1.05, 9: 1.1, 10: 1.15, 11: 1.1, 12: 1.1
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.94,
                    "West Bengal": 1.03,
                }
            ),
            "okra": CommodityPriceData(
                base_price=30.0,
                seasonal_factors={
                    1: 1.2, 2: 1.15, 3: 1.0, 4: 0.9, 5: 0.85, 6: 0.9,
                    7: 0.95, 8: 1.0, 9: 1.1, 10: 1.15, 11: 1.2, 12: 1.2
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.94, "Tamil Nadu": 1.06,
                    "Andhra Pradesh": 0.97, "Telangana": 0.96, "Gujarat": 1.04,
                    "Madhya Pradesh": 0.93, "Rajasthan": 1.08, "Uttar Pradesh": 0.92,
                    "West Bengal": 1.05,
                }
            ),
            "green_chilli": CommodityPriceData(
                base_price=35.0,
                seasonal_factors={
                    1: 1.15, 2: 1.1, 3: 1.0, 4: 0.95, 5: 0.9, 6: 0.95,
                    7: 1.0, 8: 1.05, 9: 1.1, 10: 1.15, 11: 1.2, 12: 1.15
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.93, "Tamil Nadu": 1.07,
                    "Andhra Pradesh": 0.96, "Telangana": 0.95, "Gujarat": 1.05,
                    "Madhya Pradesh": 0.92, "Rajasthan": 1.09, "Uttar Pradesh": 0.94,
                    "West Bengal": 1.04,
                }
            ),
            # Grains and Cereals
            "rice": CommodityPriceData(
                base_price=35.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.15, 9: 1.1, 10: 1.05, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.94, "Tamil Nadu": 1.02,
                    "Andhra Pradesh": 0.96, "Telangana": 0.95, "Gujarat": 1.06,
                    "Madhya Pradesh": 0.98, "Rajasthan": 1.08, "Uttar Pradesh": 0.97,
                    "West Bengal": 0.92,
                }
            ),
            "wheat": CommodityPriceData(
                base_price=28.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.9, 4: 0.9, 5: 0.95, 6: 1.0,
                    7: 1.05, 8: 1.1, 9: 1.1, 10: 1.05, 11: 1.0, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.98, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.97, "Telangana": 0.96, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.93,
                    "West Bengal": 1.03,
                }
            ),
            "maize": CommodityPriceData(
                base_price=22.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.94, "Rajasthan": 1.07, "Uttar Pradesh": 0.95,
                    "West Bengal": 1.02,
                }
            ),
            "bajra": CommodityPriceData(
                base_price=26.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.1,
                    7: 1.15, 8: 1.1, 9: 1.05, 10: 1.0, 11: 0.95, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.97, "Tamil Nadu": 1.05,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.96, "Rajasthan": 1.04, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.06,
                }
            ),
            # Pulses
            "tur_dal": CommodityPriceData(
                base_price=85.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "moong_dal": CommodityPriceData(
                base_price=95.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.1,
                    7: 1.1, 8: 1.05, 9: 1.0, 10: 0.95, 11: 0.95, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.97, "Tamil Nadu": 1.03,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.96, "Rajasthan": 1.05, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.01,
                }
            ),
            "urad_dal": CommodityPriceData(
                base_price=90.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "chana_dal": CommodityPriceData(
                base_price=75.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.1,
                    7: 1.1, 8: 1.05, 9: 1.0, 10: 0.95, 11: 0.95, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.97, "Tamil Nadu": 1.03,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.96, "Rajasthan": 1.05, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.01,
                }
            ),
            # Fruits
            "mango": CommodityPriceData(
                base_price=60.0,
                seasonal_factors={
                    1: 1.3, 2: 1.2, 3: 0.8, 4: 0.7, 5: 0.75, 6: 0.9,
                    7: 1.1, 8: 1.2, 9: 1.25, 10: 1.3, 11: 1.3, 12: 1.3
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.94, "Tamil Nadu": 1.06,
                    "Andhra Pradesh": 0.96, "Telangana": 0.95, "Gujarat": 1.04,
                    "Madhya Pradesh": 0.98, "Rajasthan": 1.08, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.03,
                }
            ),
            "banana": CommodityPriceData(
                base_price=40.0,
                seasonal_factors={
                    1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
                    7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.95, "Tamil Nadu": 0.92,
                    "Andhra Pradesh": 0.94, "Telangana": 0.96, "Gujarat": 1.05,
                    "Madhya Pradesh": 1.03, "Rajasthan": 1.08, "Uttar Pradesh": 1.02,
                    "West Bengal": 1.04,
                }
            ),
            "apple": CommodityPriceData(
                base_price=120.0,
                seasonal_factors={
                    1: 1.1, 2: 1.05, 3: 1.0, 4: 0.95, 5: 0.95, 6: 1.0,
                    7: 1.05, 8: 1.1, 9: 1.15, 10: 1.1, 11: 1.05, 12: 1.1
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.98, "Tamil Nadu": 1.02,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.01,
                    "Madhya Pradesh": 0.97, "Rajasthan": 1.04, "Uttar Pradesh": 0.96,
                    "West Bengal": 1.03,
                }
            ),
            "orange": CommodityPriceData(
                base_price=50.0,
                seasonal_factors={
                    1: 0.85, 2: 0.9, 3: 0.95, 4: 1.0, 5: 1.1, 6: 1.2,
                    7: 1.25, 8: 1.2, 9: 1.1, 10: 1.0, 11: 0.95, 12: 0.85
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "grapes": CommodityPriceData(
                base_price=70.0,
                seasonal_factors={
                    1: 0.9, 2: 0.85, 3: 0.9, 4: 1.0, 5: 1.1, 6: 1.15,
                    7: 1.2, 8: 1.15, 9: 1.1, 10: 1.0, 11: 0.95, 12: 0.9
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.94, "Tamil Nadu": 1.06,
                    "Andhra Pradesh": 0.97, "Telangana": 0.96, "Gujarat": 1.04,
                    "Madhya Pradesh": 0.98, "Rajasthan": 1.08, "Uttar Pradesh": 0.99,
                    "West Bengal": 1.05,
                }
            ),
            "pomegranate": CommodityPriceData(
                base_price=90.0,
                seasonal_factors={
                    1: 1.1, 2: 1.05, 3: 1.0, 4: 0.95, 5: 0.95, 6: 1.0,
                    7: 1.05, 8: 1.1, 9: 1.15, 10: 1.1, 11: 1.05, 12: 1.1
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.95, "Tamil Nadu": 1.05,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.96, "Rajasthan": 1.07, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.04,
                }
            ),
            "papaya": CommodityPriceData(
                base_price=25.0,
                seasonal_factors={
                    1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
                    7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "watermelon": CommodityPriceData(
                base_price=15.0,
                seasonal_factors={
                    1: 1.2, 2: 1.15, 3: 0.9, 4: 0.8, 5: 0.85, 6: 0.95,
                    7: 1.05, 8: 1.1, 9: 1.15, 10: 1.2, 11: 1.2, 12: 1.2
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.95, "Tamil Nadu": 1.05,
                    "Andhra Pradesh": 0.97, "Telangana": 0.96, "Gujarat": 1.04,
                    "Madhya Pradesh": 0.98, "Rajasthan": 1.07, "Uttar Pradesh": 0.99,
                    "West Bengal": 1.03,
                }
            ),
            # Leafy Vegetables
            "spinach": CommodityPriceData(
                base_price=20.0,
                seasonal_factors={
                    1: 0.85, 2: 0.9, 3: 0.95, 4: 1.05, 5: 1.15, 6: 1.2,
                    7: 1.15, 8: 1.1, 9: 1.0, 10: 0.95, 11: 0.9, 12: 0.85
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "coriander": CommodityPriceData(
                base_price=30.0,
                seasonal_factors={
                    1: 0.9, 2: 0.95, 3: 1.0, 4: 1.05, 5: 1.1, 6: 1.15,
                    7: 1.1, 8: 1.05, 9: 1.0, 10: 0.95, 11: 0.9, 12: 0.9
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.95, "Tamil Nadu": 1.05,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.96, "Rajasthan": 1.07, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.02,
                }
            ),
            "fenugreek": CommodityPriceData(
                base_price=25.0,
                seasonal_factors={
                    1: 0.85, 2: 0.9, 3: 0.95, 4: 1.05, 5: 1.15, 6: 1.2,
                    7: 1.15, 8: 1.1, 9: 1.0, 10: 0.95, 11: 0.9, 12: 0.85
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            # Spices and Condiments
            "turmeric": CommodityPriceData(
                base_price=150.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.94, "Telangana": 0.93, "Gujarat": 1.06,
                    "Madhya Pradesh": 0.98, "Rajasthan": 1.08, "Uttar Pradesh": 0.99,
                    "West Bengal": 1.05,
                }
            ),
            "ginger": CommodityPriceData(
                base_price=80.0,
                seasonal_factors={
                    1: 1.1, 2: 1.05, 3: 1.0, 4: 0.95, 5: 0.95, 6: 1.0,
                    7: 1.05, 8: 1.1, 9: 1.15, 10: 1.1, 11: 1.05, 12: 1.1
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.95, "Tamil Nadu": 1.05,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.96, "Rajasthan": 1.07, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.04,
                }
            ),
            "garlic": CommodityPriceData(
                base_price=100.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.9, 4: 0.9, 5: 0.95, 6: 1.0,
                    7: 1.05, 8: 1.1, 9: 1.1, 10: 1.05, 11: 1.0, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.97, "Tamil Nadu": 1.03,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.96, "Rajasthan": 1.05, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.01,
                }
            ),
            "cumin": CommodityPriceData(
                base_price=400.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.1,
                    7: 1.1, 8: 1.05, 9: 1.0, 10: 0.95, 11: 0.95, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.98, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 0.96,
                    "Madhya Pradesh": 0.97, "Rajasthan": 0.94, "Uttar Pradesh": 0.99,
                    "West Bengal": 1.05,
                }
            ),
            "coriander_seeds": CommodityPriceData(
                base_price=200.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.97, "Tamil Nadu": 1.03,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.96, "Rajasthan": 1.05, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.04,
                }
            ),
            # Oilseeds
            "groundnut": CommodityPriceData(
                base_price=65.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 0.95,
                    "Madhya Pradesh": 0.99, "Rajasthan": 1.06, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.03,
                }
            ),
            "soybean": CommodityPriceData(
                base_price=45.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.1,
                    7: 1.1, 8: 1.05, 9: 1.0, 10: 0.95, 11: 0.95, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.97, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.03,
                }
            ),
            "sunflower": CommodityPriceData(
                base_price=55.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.98,
                    "West Bengal": 1.02,
                }
            ),
            "mustard": CommodityPriceData(
                base_price=70.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.9, 4: 0.9, 5: 0.95, 6: 1.0,
                    7: 1.05, 8: 1.1, 9: 1.1, 10: 1.05, 11: 1.0, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.98, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.02,
                    "Madhya Pradesh": 0.96, "Rajasthan": 0.94, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.03,
                }
            ),
            # Cash Crops
            "cotton": CommodityPriceData(
                base_price=55.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.15, 9: 1.1, 10: 1.05, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.97, "Tamil Nadu": 1.03,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 0.96,
                    "Madhya Pradesh": 0.98, "Rajasthan": 1.05, "Uttar Pradesh": 0.99,
                    "West Bengal": 1.04,
                }
            ),
            "sugarcane": CommodityPriceData(
                base_price=3.0,
                seasonal_factors={
                    1: 0.95, 2: 0.95, 3: 1.0, 4: 1.05, 5: 1.1, 6: 1.1,
                    7: 1.05, 8: 1.0, 9: 0.95, 10: 0.95, 11: 0.95, 12: 0.95
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.98, "Tamil Nadu": 1.02,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 1.01,
                    "Madhya Pradesh": 0.97, "Rajasthan": 1.04, "Uttar Pradesh": 0.96,
                    "West Bengal": 1.03,
                }
            ),
            "jute": CommodityPriceData(
                base_price=40.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.1,
                    7: 1.15, 8: 1.1, 9: 1.05, 10: 1.0, 11: 0.95, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.02, "Karnataka": 1.04, "Tamil Nadu": 1.05,
                    "Andhra Pradesh": 1.03, "Telangana": 1.04, "Gujarat": 1.06,
                    "Madhya Pradesh": 1.03, "Rajasthan": 1.08, "Uttar Pradesh": 1.02,
                    "West Bengal": 0.95,
                }
            ),
            # Additional Vegetables
            "bitter_gourd": CommodityPriceData(
                base_price=32.0,
                seasonal_factors={
                    1: 1.15, 2: 1.1, 3: 1.0, 4: 0.95, 5: 0.9, 6: 0.95,
                    7: 1.0, 8: 1.05, 9: 1.1, 10: 1.15, 11: 1.15, 12: 1.15
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "bottle_gourd": CommodityPriceData(
                base_price=18.0,
                seasonal_factors={
                    1: 1.1, 2: 1.05, 3: 1.0, 4: 0.95, 5: 0.9, 6: 0.95,
                    7: 1.0, 8: 1.05, 9: 1.1, 10: 1.1, 11: 1.1, 12: 1.1
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "ridge_gourd": CommodityPriceData(
                base_price=26.0,
                seasonal_factors={
                    1: 1.15, 2: 1.1, 3: 1.0, 4: 0.95, 5: 0.9, 6: 0.95,
                    7: 1.0, 8: 1.05, 9: 1.1, 10: 1.15, 11: 1.15, 12: 1.15
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "pumpkin": CommodityPriceData(
                base_price=16.0,
                seasonal_factors={
                    1: 1.1, 2: 1.05, 3: 1.0, 4: 0.95, 5: 0.95, 6: 1.0,
                    7: 1.05, 8: 1.1, 9: 1.1, 10: 1.1, 11: 1.05, 12: 1.1
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "radish": CommodityPriceData(
                base_price=14.0,
                seasonal_factors={
                    1: 0.85, 2: 0.9, 3: 0.95, 4: 1.05, 5: 1.15, 6: 1.2,
                    7: 1.15, 8: 1.1, 9: 1.0, 10: 0.95, 11: 0.9, 12: 0.85
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            "beetroot": CommodityPriceData(
                base_price=22.0,
                seasonal_factors={
                    1: 0.9, 2: 0.95, 3: 1.0, 4: 1.05, 5: 1.1, 6: 1.15,
                    7: 1.1, 8: 1.05, 9: 1.0, 10: 0.95, 11: 0.9, 12: 0.9
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 1.04,
                    "Andhra Pradesh": 0.98, "Telangana": 0.97, "Gujarat": 1.03,
                    "Madhya Pradesh": 0.95, "Rajasthan": 1.06, "Uttar Pradesh": 0.97,
                    "West Bengal": 1.02,
                }
            ),
            # Additional Commodities
            "coconut": CommodityPriceData(
                base_price=30.0,
                seasonal_factors={
                    1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
                    7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.94, "Tamil Nadu": 0.92,
                    "Andhra Pradesh": 0.95, "Telangana": 0.96, "Gujarat": 1.08,
                    "Madhya Pradesh": 1.10, "Rajasthan": 1.12, "Uttar Pradesh": 1.06,
                    "West Bengal": 1.04,
                }
            ),
            "sesame": CommodityPriceData(
                base_price=110.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.97, "Tamil Nadu": 1.03,
                    "Andhra Pradesh": 0.99, "Telangana": 0.98, "Gujarat": 0.96,
                    "Madhya Pradesh": 0.98, "Rajasthan": 1.05, "Uttar Pradesh": 0.99,
                    "West Bengal": 1.04,
                }
            ),
            "black_pepper": CommodityPriceData(
                base_price=600.0,
                seasonal_factors={
                    1: 1.0, 2: 0.95, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.1,
                    7: 1.1, 8: 1.05, 9: 1.0, 10: 0.95, 11: 0.95, 12: 1.0
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.96, "Tamil Nadu": 0.94,
                    "Andhra Pradesh": 0.97, "Telangana": 0.98, "Gujarat": 1.05,
                    "Madhya Pradesh": 1.06, "Rajasthan": 1.08, "Uttar Pradesh": 1.04,
                    "West Bengal": 1.03,
                }
            ),
            "cardamom": CommodityPriceData(
                base_price=1200.0,
                seasonal_factors={
                    1: 1.05, 2: 1.0, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.05,
                    7: 1.1, 8: 1.1, 9: 1.05, 10: 1.0, 11: 1.0, 12: 1.05
                },
                regional_variations={
                    "Maharashtra": 1.0, "Karnataka": 0.95, "Tamil Nadu": 0.94,
                    "Andhra Pradesh": 0.97, "Telangana": 0.98, "Gujarat": 1.06,
                    "Madhya Pradesh": 1.08, "Rajasthan": 1.10, "Uttar Pradesh": 1.05,
                    "West Bengal": 1.04,
                }
            ),
        }

    def get_seasonal_factor(self, commodity: str, month: Optional[int] = None) -> float:
        """
        Returns seasonal price adjustment factor based on month
        Simulates seasonal price variations
        
        Args:
            commodity: Name of the commodity
            month: Month (1-12), defaults to current month
            
        Returns:
            Seasonal adjustment factor (multiplier)
        """
        if month is None:
            month = datetime.now().month
        
        if commodity not in self.demo_data:
            return 1.0
        
        return self.demo_data[commodity].seasonal_factors.get(month, 1.0)
    
    def get_regional_factor(self, commodity: str, state: Optional[str] = None) -> float:
        """
        Returns regional price adjustment factor
        
        Args:
            commodity: Name of the commodity
            state: State name, defaults to Maharashtra
            
        Returns:
            Regional adjustment factor (multiplier)
        """
        if commodity not in self.demo_data:
            return 1.0
        
        if state is None:
            state = "Maharashtra"
        
        return self.demo_data[commodity].regional_variations.get(state, 1.0)

    async def get_demo_prices(
        self,
        commodity: str,
        state: Optional[str] = None,
        num_mandis: int = 3
    ) -> List[PriceData]:
        """
        Generates realistic demo price data with variation
        
        Args:
            commodity: Name of the commodity
            state: State name (optional)
            num_mandis: Number of simulated mandis to generate prices for
            
        Returns:
            List of prices from simulated mandis
        """
        if commodity not in self.demo_data:
            # Return generic price for unknown commodities
            return self._generate_generic_price(commodity, state, num_mandis)
        
        commodity_data = self.demo_data[commodity]
        base_price = commodity_data.base_price
        seasonal_factor = self.get_seasonal_factor(commodity)
        regional_factor = self.get_regional_factor(commodity, state)
        
        # Generate prices for multiple simulated mandis
        prices = []
        for i in range(num_mandis):
            # Add random variation (±10%)
            variation = random.uniform(
                1 - self.price_variation,
                1 + self.price_variation
            )
            price = base_price * seasonal_factor * regional_factor * variation
            
            prices.append(PriceData(
                commodity=commodity,
                price=round(price, 2),
                unit="kg",
                source=PriceSource.DEMO,
                location=Location(
                    state=state or "Maharashtra",
                    district=f"Demo District {i+1}"
                ),
                mandi_name=f"Demo Mandi {i+1}",
                timestamp=datetime.now(),
                is_demo=True
            ))
        
        return prices
    
    def _generate_generic_price(
        self,
        commodity: str,
        state: Optional[str] = None,
        num_mandis: int = 3
    ) -> List[PriceData]:
        """
        Generates generic price for unknown commodities
        Uses a base price of 20 Rs/kg with variation
        
        Args:
            commodity: Name of the commodity
            state: State name (optional)
            num_mandis: Number of simulated mandis
            
        Returns:
            List of generic prices
        """
        base_price = 20.0
        prices = []
        
        for i in range(num_mandis):
            # Add wider variation for unknown commodities (±20%)
            variation = random.uniform(0.8, 1.2)
            
            prices.append(PriceData(
                commodity=commodity,
                price=round(base_price * variation, 2),
                unit="kg",
                source=PriceSource.DEMO,
                location=Location(
                    state=state or "Maharashtra",
                    district=f"Demo District {i+1}"
                ),
                mandi_name=f"Demo Mandi {i+1}",
                timestamp=datetime.now(),
                is_demo=True
            ))
        
        return prices
    
    def get_supported_commodities(self) -> List[str]:
        """
        Returns list of all supported commodities
        
        Returns:
            List of commodity names
        """
        return list(self.demo_data.keys())
    
    def is_commodity_supported(self, commodity: str) -> bool:
        """
        Checks if a commodity is in the demo data
        
        Args:
            commodity: Name of the commodity
            
        Returns:
            True if commodity is supported, False otherwise
        """
        return commodity in self.demo_data
