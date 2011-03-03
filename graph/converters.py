import datetime
import simplejson

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
            if not key.startswith('_'):
                if key not in node_attributes:
                    node_attributes[key] = attribute_counter
                    attribute_counter += 1
                nodes += """
                    <attvalue for="%s" value="%s"/>""" % (node_attributes[key],
                                                            value)
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
            if key != "node1" and key != "node2" and not key.startswith('_'):
                if key not in edge_attributes:
                    edge_attributes[key] = attribute_counter
                    attribute_counter += 1
                edges += """
                    <attvalue for="%s" value="%s"/>""" % (edge_attributes[key],
                                                            value)
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