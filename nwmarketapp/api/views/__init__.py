from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from rest_framework.decorators import api_view, renderer_classes, schema
from rest_framework import response, schemas


@api_view()
@renderer_classes([SwaggerUIRenderer, OpenAPIRenderer])
@schema(None)
def schema_view(request):
    generator = schemas.SchemaGenerator(title='API Documentation')
    schema = generator.get_schema(request=request)
    return response.Response(schema)
