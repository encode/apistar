var codec = new window.coreapi.codecs.CoreJSONCodec()
var coreJSON = window.atob('{{ base64_schema }}')
window.schema = codec.decode(coreJSON)
