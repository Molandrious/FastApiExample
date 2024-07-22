from database.models import ProductORM


def clear_product_dates(product: ProductORM) -> None:
    del product.created_at
    del product.updated_at
    for filter in product.filters:
        del filter.created_at
        del filter.updated_at
        # if filter.group:
        #     del filter.group.created_at
        #     del filter.group.updated_at
