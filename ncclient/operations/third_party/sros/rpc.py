from ncclient.xml_ import yang_action, SROS_GLOBAL_OPS_NS, sub_ele

from ncclient.operations.rpc import RPC


def global_operations(node):
    """Instantiate an SR OS global operation action element

    Args:
        node: A string representing the top-level action for a
            given global operation.
    Returns:
        A tuple of 'lxml.etree._Element' values.  The first value
        represents the top-level YANG action element and the second
        represents the caller supplied initial node.
    """
    parent, child = yang_action('global-operations',
                                attrs={'xmlns': SROS_GLOBAL_OPS_NS})
    ele = sub_ele(child, node)
    return (parent, ele)


class MdCliRawCommand(RPC):
    def request(self, command=None):
        node, raw_cmd_node = global_operations('md-cli-raw-command')
        sub_ele(raw_cmd_node, 'md-cli-input-line').text = command
        self._huge_tree = True
        return self._request(node)


class MdCompare(RPC):
    def _handle_target(self, target_node, target_node_type, target_node_value):
        if target_node_type == "configuration_region":
            sub_ele(target_node, target_node_value)
        elif target_node_type == "url":
            sub_ele(target_node, 'url').text = target_node_value
        elif target_node_type == "rollback":
            rollback_node = sub_ele(target_node, "rollback")
            sub_ele(rollback_node, "checkpoint-id").text = target_node_value
        else:
            assert False, f"{target_node_type} is not a known type."

    def _handle_path(self, md_compare_node, path):
        if path != '/':
            path_node = sub_ele(md_compare_node, 'path')
            subtree_path_node = sub_ele(path_node, 'subtree-path')
            append_node = subtree_path_node
            if path[0] == '/':
                path = path[1:]
            if path.split('/')[0] == "configure":
                append_node = sub_ele(append_node,
                                     'configure',
                                      attrs={"xmlns": "urn:nokia.com:sros:ns:yang:sr:conf"})
            else:
                assert False,\
                    "Compare takes a path starting with 'configure'," +\
                    f"not {path.split('/')[0]}"

            for i in path.split('/')[1:-1]:
                if i:
                    append_node = sub_ele(append_node, i)
            # just to have a <tag></tag>, otherwise its going to be <tag/>
            sub_ele(append_node, path.split('/')[-1]).text = ""

    def request(self, src="baseline",
                src_type="configuration_region",
                dst="candidate",
                dst_type="url",
                response_format='xml',
                configuration_region="configure",
                path='/'):
        assert response_format in ["xml", "md-cli"],\
            "Must use one of xml, json or md-cli for format. Default is 'xml'."
        node, cmp_node = global_operations('md-compare')

        sub_ele(cmp_node, 'format').text = response_format

        source = sub_ele(cmp_node, 'source')
        destination = sub_ele(cmp_node, 'destination')

        self._handle_target(source, src_type, src)
        self._handle_target(destination, dst_type, dst)

        self._handle_path(cmp_node, path)

        sub_ele(cmp_node, 'configuration-region').text = configuration_region

        self._huge_tree = True
        return self._request(node)
