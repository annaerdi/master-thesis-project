import json
from playwright.sync_api import Page, ElementHandle


def build_naive_css_selector(element: ElementHandle) -> str:
    """
    naive CSS selector builder by climbing up DOM parents
    """
    return element.evaluate(
        """
        (el) => {
            function getSelector(node) {
                // If the node is the document or the HTML element, stop.
                if (!node || node.nodeType !== Node.ELEMENT_NODE) return '';
                let selector = node.tagName.toLowerCase();

                // If it has an ID, use that and stop climbing.
                if (node.id) {
                    selector += '#' + node.id;
                    return selector;
                }

                // Otherwise, if it has a class, include the first class as a partial reference.
                if (node.className) {
                    const className = node.className.trim().split(' ')[0];
                    if (className) {
                        selector += '.' + className;
                    }
                }

                const parent = node.parentElement;
                if (!parent) {
                    return selector;
                }

                // Count how many siblings of the same type precede the node.
                let index = 1;
                let sibling = node.previousElementSibling;
                while (sibling) {
                    if (sibling.tagName === node.tagName) {
                        index += 1;
                    }
                    sibling = sibling.previousElementSibling;
                }

                // Append :nth-of-type if needed.
                selector += ':nth-of-type(' + index + ')';

                // Recursively go up the tree.
                return getSelector(parent) + ' > ' + selector;
            }

            return getSelector(el);
        }
        """
    )


def collect_and_save_interactive_elements(page: Page, output_file: str) -> None:
    """
    Collects potentially interactive elements from the given Playwright Page
    and saves the collected data as JSON to `output_file`.
    """
    selectors = ["a", "button", "input", "textarea", "select"]
    joined_selectors = ",".join(selectors)
    elements = page.query_selector_all(joined_selectors)
    interactive_elements = []

    for idx, elem in enumerate(elements, start=1):
        tag_name = elem.evaluate("el => el.tagName")
        element_id = elem.get_attribute("id")
        element_class = elem.get_attribute("class")
        element_type = elem.get_attribute("type")
        element_role = elem.get_attribute("role")
        element_placeholder = elem.get_attribute("placeholder")
        element_text = elem.inner_text().strip()
        bounding_box = elem.bounding_box()  # may be None if off-screen

        css_selector = build_naive_css_selector(elem)

        record = {
            "index": idx,
            "tag": tag_name,
            "id": element_id,
            "class": element_class,
            "type": element_type,
            "role": element_role,
            "text": element_text,
            "placeholder": element_placeholder,
            "selector": f"css={css_selector}",
            "bounding_box": bounding_box
        }

        interactive_elements.append(record)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(interactive_elements, f, indent=2)

    print(f"Saved {len(interactive_elements)} interactive elements to {output_file}.")
