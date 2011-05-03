import datetime
import simplejson


htmlCodes = (
    ('&', '&amp;'),
    ('<', '&lt;'),
    ('>', '&gt;'),
    ('"', '&quot;'),
    ("'", '&#39;'),
)


def encode_html(value):
    if isinstance(value, basestring):
        for replacement in htmlCodes:
            value = value.replace(replacement[0], replacement[1])
    return value


def json_to_gexf(json_graph):
    " Converts a Sylva json graph to GEXF 1.2"
    today = datetime.datetime.now()
    date = "%s-%s-%s" % (today.year, today.month, today.day)
    graph = simplejson.loads(json_graph)
    attribute_counter = 0
    node_attributes = {}
    edge_attributes = {}
    nodes = ''
    for node, properties in graph['nodes'].iteritems():
        nodes += """
            <node id="%s" label="%s">
            <attvalues>""" % (node, node)
        for key, value in properties.iteritems():
            if key not in node_attributes:
                node_attributes[key] = attribute_counter
                attribute_counter += 1
            nodes += """
                <attvalue for="%s" value="%s"/>""" % (node_attributes[key],
                                                    encode_html(value))
        nodes += """
            </attvalues>
            </node>"""
    attribute_counter = 0
    edges = ''
    for edge in graph['edges']:
        edges += """
            <edge id="%s" source="%s" target="%s">
            <attvalues>""" % (edge,
                                graph['edges'][edge]['node1'],
                                graph['edges'][edge]['node2'])
        for key, value in graph['edges'][edge].iteritems():
            if key != "node1" and key != "node2":
                if key not in edge_attributes:
                    edge_attributes[key] = attribute_counter
                    attribute_counter += 1
                edges += """
                    <attvalue for="%s" value="%s"/>""" % (edge_attributes[key],
                                                        encode_html(value))
        edges += """
            </attvalues>
            </edge>"""
    node_attributes_xml = ''
    for key, value in node_attributes.iteritems():
        node_attributes_xml += """
            <attribute id="%s" title="%s" type="string"/>""" % (value,
                                                                key)
    edge_attributes_xml = ''
    for key, value in edge_attributes.iteritems():
        edge_attributes_xml += """
            <attribute id="%s" title="%s" type="string"/>""" % (value,
                                                                key)
    gephi_format = """<?xml version="1.0" encoding="UTF-8"?> 
<gexf xmlns="http://www.gexf.net/1.2draft" xmlns:viz="http://www.gexf.net/1.2draft/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd" version="1.2"> 
    <meta lastmodifieddate="%s"> 
        <creator>Sylva</creator> 
        <description>A Sylva exported file</description> 
    </meta> 
    <graph mode="static" defaultedgetype="directed"> 
        <attributes class="node">
            %s
        </attributes>
        <attributes class="edge">
            %s
        </attributes>
        <nodes>%s
        </nodes> 
        <edges>%s
        </edges> 
    </graph> 
</gexf>""" % (date, node_attributes_xml, edge_attributes_xml, nodes, edges)
    return gephi_format


def neo4j_to_gml(graph):
    #List of tuples with original key and new key
    node_attributes = [('_slug', 'name'),
                        ('_type', 'type')]
    edge_attributes = [('_type', 'type')]
    gml_data = ""
    gml_data += "graph [\n"
    gml_data += "comment \"Sylva exported graph\"\n"
    gml_data += "directed 1\n"
    gml_data += "IsPlanar 1\n"
    for node in graph['nodes']:
        gml_data += "node [\n"
        gml_data += "id %d\n" % node.id
        # Attributes
        for at in node_attributes:
            gml_data += '%s "%s"\n' % (at[1], node.get(at[0], ''))
        gml_data += "]\n"
    for relationship in graph['relationships']:
        gml_data += "edge [\n"
        gml_data += "source %d\n" % relationship.start.id
        gml_data += "target %d\n" % relationship.end.id
        # Attributes
        for at in edge_attributes:
            gml_data += '%s "%s"\n' % (at[1], relationship.get(at[0], ''))
        gml_data += "]\n"
    gml_data += "]\n"
    return gml_data


def neo4j_to_gexf(graph):
    " Converts a Sylva neo4j graph to GEXF 1.2"
    today = datetime.datetime.now()
    date = "%s-%s-%s" % (today.year, today.month, today.day)
    attribute_counter = 0
    node_attributes = {}
    edge_attributes = {}
    nodes = ''
    for node in graph['nodes']:
        nodes += """
            <node id="%s" label="%s">
            <attvalues>""" % (node.id, node['_slug'])
        for key, value in node.properties.iteritems():
            if key not in node_attributes:
                node_attributes[key] = attribute_counter
                attribute_counter += 1
            nodes += """
                <attvalue for="%s" value="%s"/>""" % (node_attributes[key],
                                                    encode_html(value))
        nodes += """
            </attvalues>
            </node>"""
    attribute_counter = 0
    edges = ''
    for edge in graph['relationships']:
        edges += """
            <edge id="%s" source="%s" target="%s">
            <attvalues>""" % (edge.id, 
                                edge.start.id,
                                edge.end.id)
        for key, value in edge.properties.iteritems():
            if key not in edge_attributes:
                edge_attributes[key] = attribute_counter
                attribute_counter += 1
            edges += """
                <attvalue for="%s" value="%s"/>""" % (edge_attributes[key],
                                                        encode_html(value))
        edges += """
            </attvalues>
            </edge>"""
    node_attributes_xml = ''
    for key, value in node_attributes.iteritems():
        node_attributes_xml += """
            <attribute id="%s" title="%s" type="string"/>""" % (value,
                                                                key)
    edge_attributes_xml = ''
    for key, value in edge_attributes.iteritems():
        edge_attributes_xml += """
            <attribute id="%s" title="%s" type="string"/>""" % (value,
                                                                key)
    gephi_format = """<?xml version="1.0" encoding="UTF-8"?> 
<gexf xmlns="http://www.gexf.net/1.2draft" xmlns:viz="http://www.gexf.net/1.2draft/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd" version="1.2"> 
    <meta lastmodifieddate="%s"> 
        <creator>Sylva</creator> 
        <description>A Sylva exported file</description> 
    </meta> 
    <graph mode="static" defaultedgetype="directed"> 
        <attributes class="node">
            %s
        </attributes>
        <attributes class="edge">
            %s
        </attributes>
        <nodes>%s
        </nodes> 
        <edges>%s
        </edges> 
    </graph> 
</gexf>""" % (date, node_attributes_xml, edge_attributes_xml, nodes, edges)
    return gephi_format
