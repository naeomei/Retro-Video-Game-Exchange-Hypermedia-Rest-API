import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import User, Game
from app.auth import get_password_hash


def create_sample_data():
    """
    Create sample users and games in the database for testing.

    This script creates:
    - 3 sample users with hashed passwords
    - 3 games distributed among the users (Minecraft, Animal Crossing, Among Us)
    """
    Base.metadata.create_all(bind=engine)

    database_session = SessionLocal()

    try:
        existing_users = database_session.query(User).count()
        if existing_users > 0:
            print(f"Database already has {existing_users} users. Skipping seed data creation.")
            return

        print("Creating sample data...")

        users_data = [
            {
                "name": "Alice Gamer",
                "email": "alice@example.com",
                "password": get_password_hash("gamer123"),
                "street_address": "123 Minecraft Lane, Blockville"
            },
            {
                "name": "Bob Trader",
                "email": "bob@example.com",
                "password": get_password_hash("trader456"),
                "street_address": "456 Island Road, Paradise Isle"
            },
            {
                "name": "Carol Swapper",
                "email": "carol@example.com",
                "password": get_password_hash("swapper789"),
                "street_address": "789 Space Station, Orbit City"
            }
        ]

        created_users = []
        for user_data in users_data:
            user = User(**user_data)
            database_session.add(user)
            database_session.flush() 
            created_users.append(user)
            print(f"  Created user: {user.name} ({user.email})")

        # Create sample games
        # Alice owns Minecraft
        # Bob owns Animal Crossing: New Horizons
        # Carol owns Among Us
        games_data = [
            {
                "name": "Minecraft",
                "publisher": "Mojang Studios",
                "year_published": 2011,
                "system": "Multi-platform",
                "condition": "good",
                "previous_owners": 2,
                "owner_id": created_users[0].id
            },
            {
                "name": "Animal Crossing: New Horizons",
                "publisher": "Nintendo",
                "year_published": 2020,
                "system": "Switch",
                "condition": "mint",
                "previous_owners": 0,
                "owner_id": created_users[1].id
            },
            {
                "name": "Among Us",
                "publisher": "InnerSloth",
                "year_published": 2018,
                "system": "Multi-platform",
                "condition": "fair",
                "previous_owners": 1,
                "owner_id": created_users[2].id
            }
        ]

        for game_data in games_data:
            game = Game(**game_data)
            database_session.add(game)
            owner_name = next(u.name for u in created_users if u.id == game_data["owner_id"])
            print(f"  Created game: {game.name} (owned by {owner_name})")

        database_session.commit()
        print("\nSample data created successfully!")
        print("\nTest credentials:")
        print("  alice@example.com / gamer123 (owns Minecraft)")
        print("  bob@example.com / trader456 (owns Animal Crossing: New Horizons)")
        print("  carol@example.com / swapper789 (owns Among Us)")

    except Exception as error:
        print(f"Error creating sample data: {error}")
        database_session.rollback()
        raise
    finally:
        database_session.close()


if __name__ == "__main__":
    create_sample_data()
