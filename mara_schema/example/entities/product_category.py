from mara_schema.entity import Entity

product_category_entity = Entity(
    name='Product category',
    description='A broad categorization of products as defined by the purchasing team',
    schema_name='dim')

product_category_entity.add_attribute(
    name='Level 1',
    description='One of the 6 main product categories',
    column_name='main_category')

product_category_entity.add_attribute(
    name='Level 2',
    description='The second level category of a product',
    column_name='sub_category_1')
