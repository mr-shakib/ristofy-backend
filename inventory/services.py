from collections import defaultdict
from decimal import Decimal

from .models import RecipeComponent, StockMovement


def consume_stock_for_order_items(*, order, order_items, actor_user=None):
    """Deduct ingredient stock for fired order items using active recipe components."""
    menu_item_ids = {item.menu_item_id for item in order_items if item.menu_item_id}
    if not menu_item_ids:
        return []

    components = (
        RecipeComponent.objects.filter(
            tenant=order.tenant,
            branch=order.branch,
            menu_item_id__in=menu_item_ids,
            is_active=True,
        )
        .select_related("ingredient")
        .order_by("ingredient_id")
    )

    recipe_map = defaultdict(list)
    for component in components:
        recipe_map[component.menu_item_id].append(component)

    ingredient_totals = defaultdict(lambda: Decimal("0"))
    ingredient_ref = {}
    for item in order_items:
        if not item.menu_item_id:
            continue
        for component in recipe_map.get(item.menu_item_id, []):
            ingredient_totals[component.ingredient_id] += component.quantity * Decimal(item.quantity)
            ingredient_ref[component.ingredient_id] = component.ingredient

    movements = []
    for ingredient_id in sorted(ingredient_totals.keys()):
        quantity = ingredient_totals[ingredient_id]
        if quantity <= 0:
            continue
        ingredient = ingredient_ref[ingredient_id]
        movement = StockMovement.record_movement(
            ingredient=ingredient,
            movement_type=StockMovement.MovementType.STOCK_OUT,
            quantity=quantity,
            created_by=actor_user,
            reason="Auto deduction on order fire",
            reference=f"ORDER:{order.id}",
        )
        movements.append(movement)

    return movements
