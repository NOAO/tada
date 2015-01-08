<!--
######################################################################
PURPOSE:  For diagnostics; convert retrieved schedule (XML format) into HTML

EXAMPLES:
  xsltproc foo.xsl in.xml > out.xml

INPUT:
  Statisfies: foo.xsd

OUTPUT:
  Statisfies: bar.xsd

AUTHORS: S.Pothier
######################################################################
-->


<xsl:stylesheet	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:noao="http://www.noao.edu/proposal/noao/"
		xmlns:gemini="http://www.noao.edu/proposal/gemini/"
		version="1.0">

<xsl:output
  method="html"
  indent="yes"
  omit-xml-declaration="no"
  />

<xsl:strip-space elements="*"/> 

<xsl:template match="/">
  <html>
    <table border="1">
      <tr>
	<th>PropID</th>
	<th>period</th>
	<th>type</th>
	<th>First Name</th>
	<th>Last Name</th>
	<th>Affiliation</th>
	<th>Title</th>
      </tr>
      <xsl:apply-templates select="//records"/>
    </table>
  </html>
</xsl:template>

<xsl:template match="records">
    <xsl:apply-templates select="proposal[1]"/>
</xsl:template>

<xsl:template match="proposal[1]">
  <tr>
    <td><xsl:value-of select="@noao:id"/></td>
    <td><xsl:value-of select="noao:runs/noao:configuration[1]/parameter[@noao:type='proprietaryPeriod']"/></td>
    <td><xsl:value-of select="@noao:type"/></td>
    <td><xsl:value-of select="investigators/investigator[1]/name/first"/></td>
    <td><xsl:value-of select="investigators/investigator[1]/name/last"/></td>
    <td><xsl:value-of select="investigators/investigator[1]/affiliation"/></td>
    <td><xsl:value-of select="title"/></td>
  </tr>
</xsl:template>

<xsl:template match="//query">
</xsl:template>


</xsl:stylesheet>
