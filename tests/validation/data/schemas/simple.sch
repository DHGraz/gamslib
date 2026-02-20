<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt"
    schemaVersion="ISO Schematron 2013">
  <pattern id="simple">
    <rule context="products">
      <assert test="product">The document root must contain a 'product' element.</assert>
    </rule>
    <rule context="products/*">
      <assert test="local-name() = 'product'">Only 'product' nodes are allowed inside of 'products'</assert>
    </rule>
  </pattern>
</schema>
