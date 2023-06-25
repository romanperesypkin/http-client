"""Module for serializers and deserializers."""


def pedantic_serialize(request):
    """Pedantic to json serialization.

    :param request: pedantic to send
    :return: json response
    """
    return request.json(ensure_ascii=False)
