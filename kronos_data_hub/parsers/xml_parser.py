"""KRONOS_DATA_HUB - XML Parser"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import re

class XMLParser:
    def __init__(self):
        self.errors = []

    def parse(self, data):
        try:
            root = ET.fromstring(data)
            return self._element_to_dict(root)
        except ET.ParseError as e:
            self.errors.append(f"XML parse error: {e}")
            return None
        except Exception as e:
            self.errors.append(f"Unexpected error: {e}")
            return None

    def _element_to_dict(self, element):
        result = {}
        if element.attrib:
            result.update({f"@{k}": v for k, v in element.attrib.items()})
        if element.text and element.text.strip():
            text = element.text.strip()
            if not result:
                return text
            result["#text"] = text
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_data = self._element_to_dict(child)
                tag = self._clean_tag(child.tag)
                if tag in child_dict:
                    if not isinstance(child_dict[tag], list):
                        child_dict[tag] = [child_dict[tag]]
                    child_dict[tag].append(child_data)
                else:
                    child_dict[tag] = child_data
            if result and "#text" in result:
                result["children"] = child_dict
            else:
                result.update(child_dict)
        return result

    def _clean_tag(self, tag):
        return re.sub(r'\{[^}]+\}', '', tag)

    def parse_file(self, filepath):
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            return self._element_to_dict(root)
        except Exception as e:
            self.errors.append(f"File parse error: {e}")
            return None

    def find_all(self, data, key):
        results = []
        self._find_recursive(data, key, results)
        return results

    def _find_recursive(self, data, key, results):
        if isinstance(data, dict):
            for k, v in data.items():
                if k == key or k.endswith(f":{key}"):
                    results.append(v)
                self._find_recursive(v, key, results)
        elif isinstance(data, list):
            for item in data:
                self._find_recursive(item, key, results)
