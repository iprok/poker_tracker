"""
Database initialization module.

This module imports all entity models and initializes the database tables.
It must be imported before using the database to ensure all tables are created.
"""

from engine import Base, Engine

# Import all models to register them with Base metadata
# This ensures SQLAlchemy knows about all tables and their relationships
from domain.entity.player import Player
from domain.entity.game import Game
from domain.entity.player_action import PlayerAction
from domain.entity.tournament import Tournament
from domain.entity.player_tournament_action import PlayerTournamentAction


def init_db():
    """Initialize database by creating all tables."""
    Base.metadata.create_all(Engine)
