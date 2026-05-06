<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2" schemaVersion="ISO Schematron 2013">
  <pattern id="feature_test">
    <rule context="products">
      <assert test="lower-case(product[1]/name) = 'phone'">Failed binding-specific test for xslt2.</assert>
    </rule>
    <rule context="products/*">
      <assert test="local-name() = 'product'">Only 'product' nodes are allowed inside of 'products'</assert>
    </rule>
  </pattern>
</schema>