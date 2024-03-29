from typing import *
from argparse import ArgumentParser
from difflib import SequenceMatcher

from bs4 import BeautifulSoup, Tag


def parse_args() -> Tuple:
    args_parser = ArgumentParser()

    args_parser.add_argument('--origin', '-o', action='store', dest='file_path_origin', required=True,
                             help='Path to the origin html document that contains the original element')

    args_parser.add_argument('--mutation', '-m', action='store', dest='file_path_mutation', required=True,
                             help='Path to diff-case HTML file to search a similar element')

    args_parser.add_argument('--element_type', '-t', action='store', dest='element_type', required=False,
                             help='Type of target element in the original page. E.g. "a", "div", etc.')

    args_parser.add_argument('--attribute_name', '-n', action='store', dest='attribute_name', required=True,
                             help='Name of an attribute of the target element. E.g. "class", "title", etc.')

    args_parser.add_argument('--attribute_value', '-v', action='store', dest='attribute_value', required=True,
                             help='Value of the attribute of the target element. E.g. "btn btn-success"')

    args = args_parser.parse_args()
    return args.file_path_origin, args.file_path_mutation, args.element_type, args.attribute_name, args.attribute_value


def read_file(file_path: str) -> str:
    with open(file_path) as file:
        contents = file.read()
        return contents


def get_soup(page_content: str, parser: str = "html.parser") -> BeautifulSoup:
    return BeautifulSoup(page_content, parser)


def __get_element_by_type(soup: BeautifulSoup,
                          element_type: str,
                          **kwargs: Dict[str, str]) -> Tag:

    element_ = soup.find_all(element_type, **kwargs)
    return element_


def __get_element_by_attribute(soup: BeautifulSoup,
                               **kwargs: Dict[str, str]) -> Tag:

    element = soup.find_all(**kwargs)
    return element


def get_original_target_element(contents_origin: str,
                                element_type: str,
                                attribute_name: str,
                                attribute_value: str) -> Tag:

    soup = get_soup(contents_origin)
    kwargs = {attribute_name: attribute_value}
    if element_type:
        target_elements = __get_element_by_type(soup, element_type, **kwargs)
    else:
        target_elements = __get_element_by_attribute(soup, **kwargs)

    qty = len(target_elements)
    assert qty == 1, f'The are {qty} elements with search criteria: {element_type, attribute_name, attribute_value}'
    return target_elements[0]


def get_all_elements(soup: BeautifulSoup) -> List[Tag]:
    return soup.find_all()


def get_generator_length(generator: Generator) -> int:
    if generator is None:
        return 0

    count = 0
    for _ in generator:
        count += 1
    return count


def get_parents_description(parents: Generator) -> str:
    output_string = ''
    for parent in parents:
        parent_string_initial = str(parent)
        parent_string_clean = ' '.join(ss.strip() for ss in parent_string_initial.split('\n'))
        output_string += ' ' if output_string else '' + parent_string_clean
    return output_string


def __get_coincidence_next_element(properties_original: Dict, properties_mutated: Dict) -> float:
    is_same_next_element_original = properties_original.get('name') == properties_original.get('next_element')
    is_same_next_element_mutation = properties_mutated.get('name') == properties_mutated.get('next_element')
    coincidence = SequenceMatcher(None, str(is_same_next_element_original), str(is_same_next_element_mutation))
    return coincidence.ratio()


def __get_coincidence_parents_description(properties_original: Dict, properties_mutated: Dict) -> float:
    parents_description_original = get_parents_description(properties_original.get('parents'))
    parents_description_mutation = get_parents_description(properties_mutated.get('parents'))
    coincidence = SequenceMatcher(None, parents_description_original, parents_description_mutation).ratio()
    if coincidence == 1:
        coincidence *= 2
    return coincidence


def __get_coincidence_parents_count(properties_original: Dict, properties_mutated: Dict) -> float:
    parents_count_original = get_generator_length(properties_original.get('parents'))
    parents_count_mutation = get_generator_length(properties_mutated.get('parents'))
    parents_counts = parents_count_original, parents_count_mutation
    coincidence = min(parents_counts) / max(parents_counts)
    return coincidence


def __get_all_keys(*args: Dict[Any, Any]) -> Set[str]:
    all_keys = []
    for dic in args:
        keys_list = list(dic)
        all_keys.extend(keys_list)
    all_keys = set(all_keys)
    return all_keys


def get_similarity(properties_original: Dict, properties_mutated: Dict) -> float:
    if properties_original.get('id') == properties_mutated.get('id'):
        return 100.

    diff_dict = dict()
    all_attr_names = __get_all_keys(properties_original, properties_mutated)

    for attr_name in all_attr_names:
        if attr_name == 'id':
            continue

        if attr_name == 'next_element':
            diff_dict[attr_name] = __get_coincidence_next_element(properties_original, properties_mutated)
            continue

        if attr_name == 'parents':
            diff_dict['parents_count'] = __get_coincidence_parents_count(properties_original, properties_mutated)
            diff_dict['parents_description'] = __get_coincidence_parents_description(properties_original, properties_mutated)
            continue

        string_original = get_property_string(properties_original, attr_name)
        string_mutation = get_property_string(properties_mutated, attr_name)
        coincidence = SequenceMatcher(None, string_original, string_mutation)

        diff_dict[attr_name] = coincidence.ratio()

    all_coefficients = list(diff_dict.values())
    mean = sum(all_coefficients) / len(all_coefficients)
    return mean


def get_property_string(properties: Dict[str, str], attr_name: str) -> str:
    property_ = properties.get(attr_name)
    if property_:
        return str(property_)
    else:
        return ''


def get_essential_properties(element: Tag) -> Dict[str, Any]:
    attrs = element.attrs
    try:
        del attrs['rel']
    except KeyError:
        pass

    attrs['name'] = element.name
    attrs['hidden'] = element.hidden
    attrs['is_empty_element'] = element.is_empty_element
    attrs['next_element'] = element.next_element
    attrs['parent_name'] = element.parent.name
    attrs['text'] = element.text
    attrs['parents'] = element.parents

    for k, v in attrs.items():
        if isinstance(v, str):
            attrs[k] = get_pretty_string(v)

    return attrs


def get_pretty_string(string_: str) -> str:
    split_string = string_.split('\n')
    return ' '.join(ss.strip() for ss in split_string)


def get_pretty_attributes(element: Tag) -> str:
    attributes = element.attrs
    try:
        del attributes['parents']
    except KeyError:
        pass

    try:
        # first 10 words only
        attributes['text'] = ' '.join(attributes['text'].split()[:10])
    except KeyError:
        pass

    for attr_name, attr_value in attributes.items():
        if isinstance(attr_value, str):
            attributes[attr_name] = get_pretty_string(attr_value)

    if attributes:
        return str(attributes)
    else:
        return ''


def get_path(element: Tag) -> str:
    output_string = ''
    output_string = get_pretty_attributes(element) + output_string

    for parent in element.parents:
        properties = get_pretty_attributes(parent)

        if output_string and properties:
            output_string = '\n' + output_string
            output_string = '\n \ /' + output_string
            output_string = '\n | |' + output_string

        if properties:
            output_string = str(properties) + output_string

    return output_string


def get_best_matching_element(target_element_original: Tag,
                              contents_mutation: str) -> Tag:

    soup_mutation = get_soup(contents_mutation)
    all_elements_from_mutated_page = get_all_elements(soup_mutation)

    properties_original = get_essential_properties(target_element_original)

    best_match = {'similarity': 0,
                  'element': None}

    for element in all_elements_from_mutated_page:
        properties_mutated = get_essential_properties(element)
        similarity = get_similarity(properties_original, properties_mutated)
        if similarity > best_match['similarity']:
            best_match['similarity'] = similarity
            best_match['element'] = element

    return best_match['element']


def main():
    file_path_origin, file_path_mutation, element_type, attribute_name, attribute_value = parse_args()

    contents_origin = read_file(file_path_origin)
    contents_mutation = read_file(file_path_mutation)

    target_element_original = get_original_target_element(contents_origin, element_type, attribute_name, attribute_value)
    best_matching_element = get_best_matching_element(target_element_original, contents_mutation)
    path_to_best_match = get_path(best_matching_element)
    print(path_to_best_match)


if __name__ == '__main__':
    main()
