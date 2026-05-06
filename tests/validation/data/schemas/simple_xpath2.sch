<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xpath2" schemaVersion="ISO Schematron 2013">
  <pattern id="feature_test">
    <rule context="products">
      <assert test="every $p in product satisfies $p/price &gt; 0">Failed binding-specific test for xpath2.</assert>
    </rule>
  </pattern>
</schema>