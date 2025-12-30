
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

# Mock loguru
import sys
from unittest.mock import MagicMock
sys.modules["loguru"] = MagicMock()

try:
    from utils.xianyu_slider_stealth import XianyuSliderStealth
    
    # Mock init to avoid browser launch
    original_init = XianyuSliderStealth.__init__
    XianyuSliderStealth.__init__ = lambda self: None
    
    stealth = XianyuSliderStealth()
    stealth.pure_user_id = "test_user"
    
    # Check validity
    is_valid = stealth._check_date_validity()
    
    if is_valid:
        print("SUCCESS: Date verification passed.")
        sys.exit(0)
    else:
        print("FAILURE: Date verification failed.")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
