<?xml version="1.0" encoding="UTF-8"?>
<!-- Absätze, Sätze, Littera und Digits bis auf 8 erweitern!! --> 
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2"
    xmlns:sqf="http://www.schematron-quickfix.com/validator/process"
    xmlns="http://purl.oclc.org/dsdl/schematron">
    <ns uri="http://www.tei-c.org/ns/1.0" prefix="t"/>
    <!--TEIHeader Ruleset-->
    <pattern>
        <rule context="t:teiHeader">
            <assert
                test="//t:titleStmt/t:title[matches(., 'ABGB: §§ [0-9]+\-[0-9]+\s?\(?([0-9]+)?\)?')]"
                >The title in the titleStmt should follow the following pattern: "ABGB: §§ {range of
                paragraphs}". Also check if the whitespace is really whitespace.</assert>
        </rule>
        <rule context="t:editionStmt">
            <assert test="count(t:p) = 5">There should be 5 Paragraphs in the editionStmt with short
                Infos regarding the conversion and enrichment processes.</assert>
            <assert test="count(t:p/t:date) = 4">Every step of the transformation process must have
                a date.</assert>
            <assert test="t:p/t:seg/text()[matches(., '§§ [0-9]+\-[0-9]+')]">The Paragraph Range in
                the EditionStmt must follow the following pattern: §§
                {startparagraph}-{endparagraph}</assert>
        </rule>
    </pattern>
    <pattern>
        <rule context="t:editionStmt//t:date">
            <assert test="./text()[matches(., '[0-9]{2}\.[0-9]{2}\.[0-9]{4}')]">Dates must follow
                the following pattern DD.MM.YYYY.</assert>
        </rule>
    </pattern>
    <pattern>
        <rule context="t:publicationStmt">
            <assert test="t:idno[@type = 'PID'][matches(., 'o:eabgb.[0-9]+\-[0-9]+')]">Every
                publicationStmt needs an idno element with the type 'PID', where the text follows
                the following pattern: o:eabgb{range of paragraphs} e.g. o:eabgb.1-14</assert>
        </rule>
    </pattern>

    <!-- Headings Base Skeleton-->

    <pattern>
        <rule context="t:div[@ana = 'akn:heading']">
            <assert
                test="@type = 'eabgb:introduction' or @type = 'eabgb:paragraphheading' or @type = 'eabgb:sectionheading' or @type = 'eabgb:romanheading' or @type = 'eabgb:partheading'"
                > The heading is missing the right type. For paragraphs use
                'eabgb:paragraphheading', for "Hauptstücke" use 'eabgb:sectionheading', for headings
                starting with roman numerals use 'eabgb:romanheading' and for "Teil" use
                'eabgb:partheading'. </assert>
            <assert test="t:p/t:choice">The headingsection is missing the base structure - choice
                nested in a p element</assert>
            <assert test="t:p/t:choice/t:seg[1][@type = 'eabgb:original']">The section about the
                source text is missing!</assert>
            <assert test="t:p/t:choice/t:seg[2][@type = 'eabgb:suggestion']">The section about the
                suggested text is missing!</assert>
            <assert test="t:p/t:choice/t:seg[3][@type = 'eabgb:alternative']">The section about the
                alternative text is missing!</assert>
        </rule>
    </pattern>

    <!-- Paragraph Base Skeleton -->

    <pattern>
        <rule context="t:div[@ana = 'akn:paragraph']">
            <assert
                test="(@xml:id[matches(., 'p[0-9]+[a-g]?')] and @n[matches(., '§[0-9]+[a-g]?\.')]) or (@xml:id[matches(., 'pp[0-9]+[a-g]?')] and @n[matches(., '§§[0-9]+[a-g]?\-[0-9]+\.')]) or (@xml:id[matches(., 'p[0-9]+[a-g]?-?I?')] and @n[matches(., '§[0-9]+[a-g]?-?I?\.')])"
                >Either the @n attribute or the @xml:id attribute follows the wrong pattern or is
                empty. For a single paragraph the pattern of @n is: "§{paragraphnumber}.", an the
                pattern of @xml:id is: "p{paragraphnumber}. For a range of paragraphs the pattern of
                @n is: "§§{range of paragraphs}." e.g. §§123-126, and the pattern of @xml:id is:
                "pp{first paragraph of range}", e.g. pp123.</assert>
            <assert test="t:div[@ana = 'akn:intro']">The shortinformation section is
                missing!</assert>
            <assert test="t:div[@ana = 'akn:content']">The content section is missing!</assert>
        </rule>
        <!-- Skeleton paragraph intro section -->
        <rule context="t:div[@ana = 'akn:intro']">
            <assert test="@type = 'eabgb:shortinformation'">The correct value of type =
                "eabgb:shortinformation".</assert>
            <assert test="count(t:p) = 2">Every short information section has two
                p-Elements.</assert>
            <assert test="count(t:p/t:seg) = 2">Every p-Element must have a seg-Element.</assert>
        </rule>
        <rule context="t:div[@ana = 'akn:intro']/t:p[1]/t:seg">
            <assert test="@type = 'eabgb:summary'">Invalid type-value. The needed value is
                "eabgb:summary".</assert>
        </rule>
        <rule context="t:div[@ana = 'akn:intro']/t:p[2]/t:seg">
            <assert test="@type = 'eabgb:remarks'">Invalid type-value. The needed value is
                "eabgb:remarks".</assert>
        </rule>
        <!-- Skeleton paragraph content section -->
        <rule context="t:div[@ana = 'akn:content']">
            <assert test="t:p/t:choice"/>
            <assert test="//t:choice/t:seg[1][@type = 'eabgb:original']">The section about the
                source text is missing!</assert>
            <assert test="//t:choice/t:seg[2][@type = 'eabgb:suggestion']">The section about the
                suggested text is missing!</assert>
            <assert test="//t:choice/t:seg[3][@type = 'eabgb:alternative']">The section about the
                alternative text is missing!</assert>
        </rule>
    </pattern>


    <!-- Paragraphs - possibilites-->
    <pattern>
        <rule context="t:div[@ana = 'akn:content']/t:p/t:choice/t:seg">
            <assert
                test="./text()/preceding-sibling::t:idno[@ana = 'akn:num'] or ./text()/preceding-sibling::t:note or not(./text())"
                > If there is text in a paragraph-segment, it should have a dedicated idno element
                with the paragraphnumber, or - of it is a comment - it should be wrapped in an note
                element.</assert>
            <!-- test for unassigned subparagraphs in paragraph -->
            <assert
                test="not(contains(./text()[1], ' (1)')) and not(contains(./text()[2], '(1)')) and not(contains(./text()[3], '(1)')) and not(contains(./text()[1], '(2)')) and not(contains(./text()[2], '(2)')) and not(contains(./text()[3], '(2)')) and not(contains(./text()[1], '(3)')) and not(contains(./text()[2], '(3)')) and not(contains(./text()[3], '(3)')) and not(contains(./text()[1], ' (4)')) and not(contains(./text()[2], '(4)')) and not(contains(./text()[3], '(4)')) and not(contains(./text()[1], '(5)')) and not(contains(./text()[2], '(5)')) and not(contains(./text()[3], '(5)')) and not(contains(./text()[1], '(6)')) and not(contains(./text()[2], '(6)')) and not(contains(./text()[3], '(6)')) "
                >Passage is not wrapped correctly. Every Text starting with (1), (2), etc. must be annotated as a subparagraph! If there are more subparagraphs in this paragraph, check if they are annotated correctly</assert>
            <!-- test for unassigned sentence in subparagraph - might cause false alarms with cited paragraphs -->
           <assert
               test="not(contains(./text()[1], ' 1 ')) and not(contains(./text()[2], ' 1 ')) and not(contains(./text()[3], ' 1 ')) and not(contains(./text()[1], ' 2 ')) and not(contains(./text()[2], ' 2 ')) and not(contains(./text()[3], ' 2 ')) and not(contains(./text()[1], ' 3 ')) and not(contains(./text()[2], ' 3 ')) and not(contains(./text()[3], ' 3 ')) and not(contains(./text()[1], ' 4 ')) and not(contains(./text()[2], ' 4 ')) and not(contains(./text()[3], ' 4 ')) and not(contains(./text()[1], ' 5 ')) and not(contains(./text()[2], ' 5 ')) and not(contains(./text()[3], ' 5 ')) and not(contains(./text()[1], ' 6 ')) and not(contains(./text()[2], ' 6 ')) and not(contains(./text()[3], ' 6 '))"
                >Sentence is not wrapped correctly. Every Text starting with 1, 2, etc. must be annotated as a sentence!  If there are more sentences in this paragraph, check if they are annotated correctly</assert>
            <assert
                test="not(contains(./text()[1], ' a) ')) and not(contains(./text()[2], ' a) ')) and not(contains(./text()[3], ' a) ')) and not(contains(./text()[1], ' b) ')) and not(contains(./text()[2], ' b) ')) and not(contains(./text()[3], ' b) ')) and not(contains(./text()[1], ' c) ')) and not(contains(./text()[2], ' c) ')) and not(contains(./text()[3], ' c) ')) and not(contains(./text()[1], ' d) ')) and not(contains(./text()[2], ' d) ')) and not(contains(./text()[3], ' d) ')) and not(contains(./text()[1], ' e) ')) and not(contains(./text()[2], ' e) ')) and not(contains(./text()[3], ' e) ')) and not(contains(./text()[1], ' f) ')) and not(contains(./text()[2], ' f) ')) and not(contains(./text()[3], ' f) ')) and not(contains(./text()[1], ' g) ')) and not(contains(./text()[2], ' g) ')) and not(contains(./text()[3], ' g) '))"
                >A list with littera might not be wrapped correctly. Every Text starting with a), b). etc. must be annotated as eabgb:littera!  If there are more litteras in this paragraph, check if they are annotated correctly</assert>
            <assert
                test="not(contains(./text()[1], ' 1. ')) and not(contains(./text()[2], ' 1. ')) and not(contains(./text()[3], ' 1. ')) and not(contains(./text()[1], ' 2. ')) and not(contains(./text()[2], ' 2. ')) and not(contains(./text()[3], ' 2. ')) and not(contains(./text()[1], ' 3. ')) and not(contains(./text()[2], ' 3. ')) and not(contains(./text()[3], ' 3. ')) "
                >A numbered list might not be  wrapped correctly. Every Text starting with 1., 2., etc. must be annotated as eabgb:point!  If there are more numbered items in this sentence, check if they are annotated correctly</assert>
        </rule> 
        <!--Absätze -->
        <rule
            context="t:div[@ana = 'akn:content']/t:p/t:choice/t:seg/t:seg[@ana = 'akn:subparagraph']">
            <assert test="./preceding-sibling::t:idno[@ana = 'akn:num']"> Every Passage is part of a
                paragraph - before the subparagraph-seg element there needs to be an idno with the
                paragraphnumber. </assert>
            <assert test="@type = 'eabgb:passage'"> The seg element misses the right attribute value
                for @type --> eabgb:passage </assert>
            <assert test="matches(@n, '\([1-9]\)')">seg elements of the type 'eabgb:passage' need an
                @n with the passagenumber (e.g., (1)) as value.</assert>
            <assert test="./t:idno[@type = 'eabgb:passagenum']"> Every passage needs an idno element
                with @type=eabgb:passagenum. </assert>
            <!-- test for unassigned Subparagraphs in Subparagraph -->
            <assert
                test="not(contains(./text()[1], ' (1)')) and not(contains(./text()[2], '(1)')) and not(contains(./text()[3], '(1)')) and not(contains(./text()[1], '(2)')) and not(contains(./text()[2], '(2)')) and not(contains(./text()[3], '(2)')) and not(contains(./text()[1], '(3)')) and not(contains(./text()[2], '(3)')) and not(contains(./text()[3], '(3)')) and not(contains(./text()[1], ' (4)')) and not(contains(./text()[2], '(4)')) and not(contains(./text()[3], '(4)')) and not(contains(./text()[1], '(5)')) and not(contains(./text()[2], '(5)')) and not(contains(./text()[3], '(5)')) and not(contains(./text()[1], '(6)')) and not(contains(./text()[2], '(6)')) and not(contains(./text()[3], '(6)')) "
                >Passage is not wrapped correctly. Every Text starting with (1), (2), etc. must be annotated as a subparagraph! If there are more subparagraphs in this subparagraph, check if they are annotated correctly</assert>
            <!-- test for unassigned sentences in subparagraph -->
            <assert
                test="not(contains(./text()[1], ' 1 ')) and not(contains(./text()[2], ' 1 ')) and not(contains(./text()[3], ' 1 ')) and not(contains(./text()[1], ' 2 ')) and not(contains(./text()[2], ' 2 ')) and not(contains(./text()[3], ' 2 ')) and not(contains(./text()[1], ' 3 ')) and not(contains(./text()[2], ' 3 ')) and not(contains(./text()[3], ' 3 ')) and not(contains(./text()[1], ' 4 ')) and not(contains(./text()[2], ' 4 ')) and not(contains(./text()[3], ' 4 ')) and not(contains(./text()[1], ' 5 ')) and not(contains(./text()[2], ' 5 ')) and not(contains(./text()[3], ' 5 ')) and not(contains(./text()[1], ' 6 ')) and not(contains(./text()[2], ' 6 ')) and not(contains(./text()[3], ' 6 '))"
                >Sentence is not wrapped correctly. Every Text starting with 1, 2, etc. must be annotated as a sentence!  If there are more sentences in this subparagraph, check if they are annotated correctly</assert>
            <assert
                test="not(contains(./text()[1], ' a) ')) and not(contains(./text()[2], ' a) ')) and not(contains(./text()[3], ' a) ')) and not(contains(./text()[1], ' b) ')) and not(contains(./text()[2], ' b) ')) and not(contains(./text()[3], ' b) ')) and not(contains(./text()[1], ' c) ')) and not(contains(./text()[2], ' c) ')) and not(contains(./text()[3], ' c) ')) and not(contains(./text()[1], ' d) ')) and not(contains(./text()[2], ' d) ')) and not(contains(./text()[3], ' d) ')) and not(contains(./text()[1], ' e) ')) and not(contains(./text()[2], ' e) ')) and not(contains(./text()[3], ' e) ')) and not(contains(./text()[1], ' f) ')) and not(contains(./text()[2], ' f) ')) and not(contains(./text()[3], ' f) ')) and not(contains(./text()[1], ' g) ')) and not(contains(./text()[2], ' g) ')) and not(contains(./text()[3], ' g) '))"
                >A list with littera might not be wrapped correctly. Every Text starting with a), b). etc. must be annotated as eabgb:littera!  If there are more litteras in this subparagraph, check if they are annotated correctly</assert>
            <assert
                test="not(contains(./text()[1], ' 1. ')) and not(contains(./text()[2], ' 1. ')) and not(contains(./text()[3], ' 1. ')) and not(contains(./text()[1], ' 2. ')) and not(contains(./text()[2], ' 2. ')) and not(contains(./text()[3], ' 2. ')) and not(contains(./text()[1], ' 3. ')) and not(contains(./text()[2], ' 3. ')) and not(contains(./text()[3], ' 3. ')) and not(contains(./text()[1], ' 4. ')) and not(contains(./text()[2], ' 4. ')) and not(contains(./text()[3], ' 4. ')) and not(contains(./text()[1], ' 5. ')) and not(contains(./text()[2], ' 5. ')) and not(contains(./text()[3], ' 5. ')) and not(contains(./text()[1], ' 6. ')) and not(contains(./text()[2], ' 6. ')) and not(contains(./text()[3], ' 6. ')) and not(contains(./text()[1], ' 7. ')) and not(contains(./text()[2], ' 7. ')) and not(contains(./text()[3], ' 7. ')) and not(contains(./text()[1], ' 8. ')) and not(contains(./text()[2], ' 8. ')) and not(contains(./text()[3], ' 8. ')) and not(contains(./text()[1], ' 9. ')) and not(contains(./text()[2], ' 9. ')) and not(contains(./text()[3], ' 9. ')) and not(contains(./text()[1], ' 10. ')) and not(contains(./text()[2], ' 10. ')) and not(contains(./text()[3], ' 10. ')) and not(contains(./text()[1], ' 11. ')) and not(contains(./text()[2], ' 11. ')) and not(contains(./text()[3], ' 11. ')) and not(contains(./text()[1], ' 12. ')) and not(contains(./text()[2], ' 12. ')) and not(contains(./text()[3], ' 12. '))" 
                >A numbered list might not be  wrapped correctly. Every Text starting with 1., 2., etc. must be annotated as eabgb:point!  If there are more numbered items in this sentence, check if they are annotated correctly</assert>
        </rule>
        <!-- Sätze -->
        <rule context="t:s">
            <assert
                test="not(contains(./text()[1], ' a) ')) and not(contains(./text()[2], ' a) ')) and not(contains(./text()[3], ' a) ')) and not(contains(./text()[1], ' b) ')) and not(contains(./text()[2], ' b) ')) and not(contains(./text()[3], ' b) ')) and not(contains(./text()[1], ' c) ')) and not(contains(./text()[2], ' c) ')) and not(contains(./text()[3], ' c) ')) and not(contains(./text()[1], ' d) ')) and not(contains(./text()[2], ' d) ')) and not(contains(./text()[3], ' d) ')) and not(contains(./text()[1], ' e) ')) and not(contains(./text()[2], ' e) ')) and not(contains(./text()[3], ' e) ')) and not(contains(./text()[1], ' f) ')) and not(contains(./text()[2], ' f) ')) and not(contains(./text()[3], ' f) ')) and not(contains(./text()[1], ' g) ')) and not(contains(./text()[2], ' g) ')) and not(contains(./text()[3], ' g) '))"
                >A list with littera might not be wrapped correctly. Every Text starting with a), b). etc. must be annotated as eabgb:littera!  If there are more litteras in this sentence, check if they are annotated correctly</assert>
            <assert
                test="not(contains(./text()[1], ' 1. ')) and not(contains(./text()[2], ' 1. ')) and not(contains(./text()[3], ' 1. ')) and not(contains(./text()[1], ' 2. ')) and not(contains(./text()[2], ' 2. ')) and not(contains(./text()[3], ' 2. ')) and not(contains(./text()[1], ' 3. ')) and not(contains(./text()[2], ' 3. ')) and not(contains(./text()[3], ' 3. ')) "
                >A numbered list might not be  wrapped correctly. Every Text starting with 1., 2., etc. must be annotated as eabgb:point!  If there are more numbered items in this sentence, check if they are annotated correctly</assert>
        </rule>

        <!-- Notes -->
        <rule context="t:note[@ana = 'akn:authorialNote']">
            <assert
                test="not(contains(./text()[1], 'Abstimmungsbedarf:')) and not(contains(./text()[2], 'Abstimmungsbedarf:')) and not(contains(./text()[3], 'Abstimmungsbedarf:'))"
                >Seems like a "Abstimmungsbedarf" is not wrapped correctly. </assert>
            <assert test="@n">Every note needs an @n with the notenumber.</assert>
            <assert test="matches(@n, '\d+')">The number in the @n has the wrong format. Th value should follow the following pattern: {number}. </assert>
            <assert test="@type='eabgb:footnote'">the @type has the wrong value. The value must be 'eabgb:footnote'.</assert>
        </rule>

<!-- termproblems -->
        <rule context="t:seg[@type='eabgb:termproblem']">
            <assert test="./t:seg[@type='eabgb:term']">Every termproblem needs to have the respective term annotated in a seg-element with type="eabgb:term"</assert>
            <assert test="not(contains(./t:seg[@type='eabgb:term']/text(), '&quot;')) and not(contains(./t:seg[@type='eabgb:term']/text(), '!'))">The seg-element with @type='eabgb:term' is wrongly formatted; the quotationmarks and the exclamation mark need to be outside of the element.</assert>
        </rule>
               
        <!-- Numbering of things -->
        <rule context="t:idno[@type = 'eabgb:passagenum']">

            <assert test="matches(./text(), '\([1-9]\)')"> The passagenumber in the text must follow
                the following pattern: ({passagenumber}).</assert>
        </rule>

        <rule context="t:idno[@ana = 'akn:num']">
            <assert test="matches(./text(), '§ [0-9]+[a-z]?\.') or matches(./text(), '§§\s[0-9]+[a-g]?\-[0-9]+')">The paragraphnumber has to follow
                the following pattern: "§ {paragraphnumber}." or when the content are multiple paragraphs: §§ {startparagraph - endparagraph}.</assert>
            <!-- tests the pattern of the paragraphnumber -->
        </rule>
        <rule context="t:idno[@type = 'eabgb:sentencenum']">
            <assert test="matches(./text(), '[1-9]')"> The passagenumber in the text must follow the
                following pattern: ({passagenumber}).</assert>
        </rule> 
       
        <!-- Littera und Digit Rules -->
        
        <rule context="t:seg[@ana='akn:point']">
            <assert test="matches(./text()[1], '[1-9]+[a-z]?\.')"> The Pointnumber must follow the following pattern: "{1-9}." .</assert>
            <assert test="matches(@n, '[1-9]+[a-z]?\.')">Seems like the @n attribute is missing or does not have the right value. Every @n should contain the point number in the following pattern: "{1-9}.".</assert>
            <assert test="@type ='eabgb:point'">The type value has the wrong value - the value should be 'eabgb:point'.</assert>
        </rule>
        <rule context="t:seg[@ana='akn:item']">
            <assert test="matches(./text()[1], '[a-z]\)')"> The Pointnumber must follow the following pattern: "{a-z})" .</assert>    
            <assert test="@type ='eabgb:littera'">The type value has the wrong value - the value should be 'eabgb:littera'.</assert>
            <assert test="matches(@n, '[a-z]\)')">Seems like the @n attribute is missing or does not have the right value. Every @n should contain the littera in the following pattern: "{a-z})".</assert>
        </rule>

    </pattern>


</sch:schema>
