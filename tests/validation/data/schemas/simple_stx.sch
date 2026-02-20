<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="stx" schemaVersion="ISO Schematron 2013">
  <pattern id="feature_test">
    <rule context="products">
      <assert test="count(product) &gt; 0">Failed binding-specific test for stx.</assert>
    </rule>
  </pattern>
</schema>