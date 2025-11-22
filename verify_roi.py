import sys
import os

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Import Base from engine to use the same declarative base
from engine import Base
# Import PlayerAction to ensure it's registered with Base.metadata
from domain.entity.player_action import PlayerAction
from domain.service.player_statistics_service import PlayerStatisticsService

def verify():
    # Setup in-memory DB
    test_engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=test_engine)
    
    # Create tables
    Base.metadata.create_all(test_engine)
    session = Session()

    # Create dummy data
    user_id = 123
    base_time = datetime(2023, 1, 1, 10, 0, 0)

    # Day 1: Buyin 100, Quit 150. Profit 50.
    # Cumulative: Buyin 100, Quit 150. ROI = 50/100 = 50.0%
    session.add(PlayerAction(game_id=1, user_id=user_id, action="buyin", amount=100, timestamp=base_time))
    session.add(PlayerAction(game_id=1, user_id=user_id, action="quit", amount=150, timestamp=base_time + timedelta(hours=1)))

    # Day 2: Buyin 200, Quit 100. Loss 100.
    # Cumulative: Buyin 300, Quit 250. Profit -50. ROI = -50/300 = -16.666...% -> -16.7%
    session.add(PlayerAction(game_id=2, user_id=user_id, action="buyin", amount=200, timestamp=base_time + timedelta(days=1)))
    session.add(PlayerAction(game_id=2, user_id=user_id, action="quit", amount=100, timestamp=base_time + timedelta(days=1, hours=1)))

    # Day 3: Buyin 100, Quit 300. Profit 200.
    # Cumulative: Buyin 400, Quit 550. Profit 150. ROI = 150/400 = 37.5%
    session.add(PlayerAction(game_id=3, user_id=user_id, action="buyin", amount=100, timestamp=base_time + timedelta(days=2)))
    session.add(PlayerAction(game_id=3, user_id=user_id, action="quit", amount=300, timestamp=base_time + timedelta(days=2, hours=1)))

    session.commit()

    # Test Service
    service = PlayerStatisticsService(session)
    roi_history = service.get_daily_roi_history(user_id)

    print("ROI History:")
    for entry in roi_history:
        print(entry)

    expected = [
        {"date": "2023-01-01", "roi": 50.0},
        {"date": "2023-01-02", "roi": -16.7},
        {"date": "2023-01-03", "roi": 37.5},
    ]

    # Check length
    if len(roi_history) != len(expected):
        print(f"FAILED: Expected length {len(expected)}, got {len(roi_history)}")
        sys.exit(1)

    # Check content
    for i, item in enumerate(roi_history):
        if item != expected[i]:
            print(f"FAILED: At index {i}, expected {expected[i]}, got {item}")
            sys.exit(1)

    print("Verification Passed!")

if __name__ == "__main__":
    verify()
