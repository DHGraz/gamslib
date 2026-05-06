<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="exslt" schemaVersion="ISO Schematron 2013">
  <pattern id="feature_test">
    <rule context="products">
      <assert test="math:max(product/price) &gt; 0">Failed binding-specific test for exslt.</assert>
    </rule>
  </pattern>
</schema>