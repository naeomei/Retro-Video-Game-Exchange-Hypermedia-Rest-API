from app.schemas.schemas import Links


def build_user_links(user_id: int) -> Links:
    """Build HATEOAS links for a user resource"""
    return Links(
        self=f"/users/{user_id}",
        update=f"/users/{user_id}",
        delete=f"/users/{user_id}",
        games=f"/games?ownerId={user_id}"
    )


def build_game_links(game_id: int, owner_id: int) -> Links:
    """Build HATEOAS links for a game resource"""
    return Links(
        self=f"/games/{game_id}",
        update=f"/games/{game_id}",
        delete=f"/games/{game_id}",
        owner=f"/users/{owner_id}"
    )


def build_trade_offer_links(offer_id: int) -> Links:
    """
    Build HATEOAS links for a trade offer resource.

    Provides links to:
    - self: The offer's own endpoint
    - respond: For accepting or rejecting the offer (PATCH)
    - cancel: For cancelling the offer (DELETE)
    """
    return Links(
        self=f"/trade-offers/{offer_id}",
        respond=f"/trade-offers/{offer_id}",
        cancel=f"/trade-offers/{offer_id}"
    )
