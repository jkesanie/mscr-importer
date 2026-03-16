<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:person="http://example.org/person"
    xmlns:employee="http://example.org/person-v2"
    exclude-result-prefixes="xsl person">

    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="/person:persons">
        <employee:employees xmlns:employee="http://example.org/person-v2">
            <xsl:apply-templates select="person:person"/>
        </employee:employees>
    </xsl:template>

    <xsl:template match="person:person">
        <employee:employee xmlns:employee="http://example.org/person-v2">
            <xsl:attribute name="empId">
                <xsl:value-of select="concat('EMP-', @id)"/>
            </xsl:attribute>
            <xsl:attribute name="hireDate">
                <xsl:value-of select="format-date(current-date(), 'yyyy-MM-dd')"/>
            </xsl:attribute>
            
            <employee:fullName>
                <xsl:value-of select="concat(person:firstName, ' ', person:lastName)"/>
            </employee:fullName>
            
            <xsl:if test="person:age">
                <employee:dateOfBirth>
                    <xsl:value-of select="format-date(subtractYears(current-date(), person:age), 'yyyy-MM-dd')"/>
                </employee:dateOfBirth>
            </xsl:if>
            
            <employee:department>
                <xsl:value-of select="'General'"/>
            </employee:department>
            
            <employee:position>
                <xsl:value-of select="'Employee'"/>
            </employee:position>
            
            <xsl:if test="person:email">
                <employee:address xmlns:employee="http://example.org/person-v2">
                    <employee:street>
                        <xsl:value-of select="person:email"/>
                    </employee:street>
                </employee:address>
            </xsl:if>
        </employee:employee>
    </xsl:template>

</xsl:stylesheet>