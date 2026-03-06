# =============================================================================
# utils.py — HATEOAS Link Builders
# =============================================================================
# What this file does:
#   Builds the _links objects attached to every API response. This implements
#   HATEOAS (Hypermedia as the Engine of Application State) — a REST constraint
#   where responses embed links to related actions so clients don't need to
#   hardcode URLs or know the API structure upfront.
#
# Why HATEOAS matters:
#   A client that follows links from the API can navigate the whole system
#   without knowing URL patterns ahead of time. If we rename a route, we only
#   update it here — clients that follow links just work without any changes.
# =============================================================================

from app.schemas.schemas import Links


def build_user_links(user_id: int) -> Links:
    return Links(
        self=f"/users/{user_id}",
        update=f"/users/{user_id}",
        delete=f"/users/{user_id}",
        games=f"/games?ownerId={user_id}"
    )


def build_game_links(game_id: int, owner_id: int) -> Links:
    return Links(
        self=f"/games/{game_id}",
        update=f"/games/{game_id}",
        delete=f"/games/{game_id}",
        owner=f"/users/{owner_id}"
    )


def build_trade_offer_links(offer_id: int) -> Links:
    return Links(
        self=f"/trade-offers/{offer_id}",
        respond=f"/trade-offers/{offer_id}",
        cancel=f"/trade-offers/{offer_id}"
    )
