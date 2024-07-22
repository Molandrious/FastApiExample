from enum import StrEnum


class CartSectionType(StrEnum):
    STOCK = 'STOCK'
    PREORDER = 'PREORDER'
    UNAVAILABLE = 'UNAVAILABLE'


class IncrementActionType(StrEnum):
    INCREMENT = 'INCREMENT'
    DECREMENT = 'DECREMENT'
