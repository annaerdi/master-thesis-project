from src.playbookgen.utils.schema import function_to_schema
from typing import Optional, List

def test_function_with_no_args():
    def sample_func():
        '''A simple function.'''
        pass
    schema = function_to_schema(sample_func)
    assert schema['function']['name'] == 'sample_func'
    assert schema['function']['description'] == 'A simple function.'
    assert schema['function']['parameters']['properties'] == {}
    assert schema['function']['parameters']['required'] == []

def test_function_with_args_and_type_hints():
    def sample_func_with_args(name: str, age: int):
        '''A function with arguments and type hints.'''
        pass
    schema = function_to_schema(sample_func_with_args)
    assert schema['function']['name'] == 'sample_func_with_args'
    assert schema['function']['description'] == 'A function with arguments and type hints.'
    assert schema['function']['parameters']['properties']['name']['type'] == 'string'
    assert schema['function']['parameters']['properties']['age']['type'] == 'integer'
    assert 'name' in schema['function']['parameters']['required']
    assert 'age' in schema['function']['parameters']['required']

def test_function_with_default_values():
    def sample_func_with_defaults(name: str = "John", age: int = 30):
        '''A function with default values.'''
        pass
    schema = function_to_schema(sample_func_with_defaults)
    assert schema['function']['name'] == 'sample_func_with_defaults'
    assert schema['function']['description'] == 'A function with default values.'
    assert schema['function']['parameters']['properties']['name']['type'] == 'string'
    assert schema['function']['parameters']['properties']['name']['default'] == 'John'
    assert schema['function']['parameters']['properties']['age']['type'] == 'integer'
    assert schema['function']['parameters']['properties']['age']['default'] == 30
    assert 'name' not in schema['function']['parameters']['required']
    assert 'age' not in schema['function']['parameters']['required']

def test_function_with_docstring():
    def sample_func_with_docstring():
        """
        This is a sample function with a docstring.
        It has multiple lines.
        """
        pass
    schema = function_to_schema(sample_func_with_docstring)
    assert schema['function']['name'] == 'sample_func_with_docstring'
    assert schema['function']['description'] == 'This is a sample function with a docstring.\nIt has multiple lines.'
    assert schema['function']['parameters']['properties'] == {}
    assert schema['function']['parameters']['required'] == []

def test_function_with_complex_type_hints():
    def sample_func_with_complex_types(names: List[str], age: Optional[int] = None):
        '''A function with complex type hints.'''
        pass
    schema = function_to_schema(sample_func_with_complex_types)
    assert schema['function']['name'] == 'sample_func_with_complex_types'
    assert schema['function']['description'] == 'A function with complex type hints.'
    assert schema['function']['parameters']['properties']['names']['type'] == 'array'
    assert schema['function']['parameters']['properties']['names']['items']['type'] == 'string'
    assert schema['function']['parameters']['properties']['age']['type'] == 'integer'
    assert schema['function']['parameters']['properties']['age']['nullable'] == True
    assert 'names' in schema['function']['parameters']['required']
    assert 'age' not in schema['function']['parameters']['required']

from src.playbookgen.main import PlaybookState
import yaml

def test_playbook_state_add_single_step():
    state = PlaybookState()
    step1 = {"type": "action", "command": "do_something"}
    state.add_step(step1)
    assert len(state.commands) == 1
    assert state.commands[0] == step1

def test_playbook_state_add_multiple_steps():
    state = PlaybookState()
    step1 = {"type": "action", "command": "do_something"}
    step2 = {"type": "sleep", "seconds": 5}
    state.add_step(step1)
    state.add_step(step2)
    assert len(state.commands) == 2
    assert state.commands[0] == step1
    assert state.commands[1] == step2

def test_playbook_state_add_steps_maintains_order():
    state = PlaybookState()
    step1 = {"id": 1, "action": "first"}
    step2 = {"id": 2, "action": "second"}
    step3 = {"id": 3, "action": "third"}
    state.add_step(step1)
    state.add_step(step2)
    state.add_step(step3)
    assert state.commands[0]["id"] == 1
    assert state.commands[1]["id"] == 2
    assert state.commands[2]["id"] == 3

def test_playbook_state_to_yaml_empty():
    state = PlaybookState()
    expected_yaml = "commands: []\n" # As per current implementation in main.py
    assert state.to_yaml() == expected_yaml

def test_playbook_state_to_yaml_one_step():
    state = PlaybookState()
    step1 = {"type": "browser", "cmd": "visit", "url": "https://example.com"}
    state.add_step(step1)
    expected_yaml_obj = {"commands": [step1]}
    # Convert expected object to YAML string, then compare
    # This avoids issues with minor formatting differences if yaml.dump is used differently
    assert yaml.safe_load(state.to_yaml()) == expected_yaml_obj


def test_playbook_state_to_yaml_multiple_steps():
    state = PlaybookState()
    step1 = {"type": "action", "command": "do_something", "args": {"arg1": "val1"}}
    step2 = {"type": "sleep", "seconds": 5}
    step3 = {"type": "browser", "cmd": "click", "selector": "#button"}
    state.add_step(step1)
    state.add_step(step2)
    state.add_step(step3)
    
    expected_yaml_obj = {"commands": [step1, step2, step3]}
    assert yaml.safe_load(state.to_yaml()) == expected_yaml_obj

def test_playbook_state_to_yaml_formatting_and_content():
    state = PlaybookState()
    step1 = {"type": "browser", "cmd": "visit", "url": "https://example.com"}
    step2 = {"type": "action", "command": "verify_title", "expected_title": "Example Domain"}
    state.add_step(step1)
    state.add_step(step2)
    
    # Expected YAML structure based on how PyYAML typically dumps lists of dicts
    expected_yaml_str = """\
commands:
- cmd: visit
  type: browser
  url: https://example.com
- command: verify_title
  expected_title: Example Domain
  type: action
"""
    # Load both actual and expected YAML to compare content, ignoring minor formatting/ordering differences within dicts
    actual_data = yaml.safe_load(state.to_yaml())
    expected_data = yaml.safe_load(expected_yaml_str)
    
    assert actual_data == expected_data

from src.playbookgen.utils.browser_helpers import build_naive_css_selector
from unittest.mock import Mock

# Tests for build_naive_css_selector

def test_build_naive_css_selector_with_id():
    """Test that an element with an ID returns 'tag#id'."""
    mock_element = Mock()
    # Mock the result of the JavaScript evaluation within build_naive_css_selector
    mock_element.evaluate.return_value = "button#myButton"
    
    selector = build_naive_css_selector(mock_element)
    assert selector == "button#myButton"
    # Verify that evaluate was called once with the expected JS function string
    mock_element.evaluate.assert_called_once()
    args, _ = mock_element.evaluate.call_args
    js_function_str = args[0]
    assert "function getSelector(node)" in js_function_str # Check if the correct JS is being passed

def test_build_naive_css_selector_with_class():
    """Test that an element with a class returns 'tag.class:nth-of-type(n)'."""
    mock_element = Mock()
    # Mock the result of the JavaScript evaluation
    mock_element.evaluate.return_value = "div.myClass:nth-of-type(1)"
    
    selector = build_naive_css_selector(mock_element)
    assert selector == "div.myClass:nth-of-type(1)"
    mock_element.evaluate.assert_called_once()
    args, _ = mock_element.evaluate.call_args
    js_function_str = args[0]
    assert "function getSelector(node)" in js_function_str

# Tests for get_interactive_elements (from main.py) and collect_and_save_interactive_elements (from utils/browser_helpers.py)
from unittest.mock import patch, mock_open 
import json
from src.playbookgen.main import get_interactive_elements as get_interactive_elements_main
from src.playbookgen.utils.browser_helpers import collect_and_save_interactive_elements

# Tests for get_interactive_elements from src.playbookgen.main

def test_get_interactive_elements_main_no_active_session():
    """Test get_interactive_elements from main.py when no active session exists."""
    with patch('src.playbookgen.main.browser_sessions', {}):
        result = get_interactive_elements_main('non_existent_session')
        assert result == "No active session. Create one with 'visit' command first."

def test_get_interactive_elements_main_no_elements_found():
    """Test get_interactive_elements from main.py with an active session but no elements."""
    mock_page = Mock()
    mock_page.query_selector_all.return_value = []
    
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            result_json_str = get_interactive_elements_main('test_session', output_file='test_elements.json')
            
            # Assert the returned JSON string is '[]'
            assert result_json_str == "[]" 
            
            # Assert json.dump was called correctly
            mock_json_dump.assert_called_once_with([], mock_file.return_value, indent=2) # Use mock_file.return_value for the file handle
            mock_file.assert_called_once_with('test_elements.json', 'w')

def test_get_interactive_elements_main_with_elements():
    """Test get_interactive_elements from main.py with a few mock interactive elements."""
    mock_page = Mock()
    
    # Element 1: Link
    mock_element1 = Mock()
    mock_element1.evaluate.return_value = "A"  # Tag name
    mock_element1.inner_text.return_value = "Link Text 1"
    # Mock get_attribute to return different values based on the attribute name
    def element1_get_attribute(attr):
        if attr == "type": return None
        if attr == "id": return "link1"
        if attr == "class": return "class1-link"
        return None
    mock_element1.get_attribute.side_effect = element1_get_attribute

    # Element 2: Button
    mock_element2 = Mock()
    mock_element2.evaluate.return_value = "BUTTON" # Tag name
    mock_element2.inner_text.return_value = "Click Me"
    def element2_get_attribute(attr):
        if attr == "type": return "submit"
        if attr == "id": return "btn1"
        if attr == "class": return "button-class"
        return None
    mock_element2.get_attribute.side_effect = element2_get_attribute

    # Element 3: Input
    mock_element3 = Mock()
    mock_element3.evaluate.return_value = "INPUT" # Tag name
    mock_element3.inner_text.return_value = "" # Inputs usually don't have inner_text like links/buttons
    def element3_get_attribute(attr):
        if attr == "type": return "text"
        if attr == "id": return "input1"
        if attr == "class": return "input-field"
        return None
    mock_element3.get_attribute.side_effect = element3_get_attribute
    
    mock_page.query_selector_all.return_value = [mock_element1, mock_element2, mock_element3]

    expected_elements_data = [
        {
            "index": 1, "selector": "css=css_selector_for_element1", "tag": "A",  # Added "css=" prefix
            "text": "Link Text 1", "type": None, "id": "link1", "class": "class1-link"
        },
        {
            "index": 2, "selector": "css=css_selector_for_element2", "tag": "BUTTON", # Added "css=" prefix
            "text": "Click Me", "type": "submit", "id": "btn1", "class": "button-class"
        },
        {
            "index": 3, "selector": "css=css_selector_for_element3", "tag": "INPUT", # Added "css=" prefix
            "text": "", "type": "text", "id": "input1", "class": "input-field"
        }
    ]

    # Mock build_naive_css_selector from where it's used in main.py
    # Based on `from .utils.browser_helpers import build_naive_css_selector` in main.py
    # the path to patch is 'src.playbookgen.main.build_naive_css_selector'
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        with patch('src.playbookgen.main.build_naive_css_selector') as mock_build_selector:
            # Make build_naive_css_selector return different values for different elements
            mock_build_selector.side_effect = [
                "css_selector_for_element1", 
                "css_selector_for_element2", 
                "css_selector_for_element3"
            ]
            with patch('builtins.open', mock_open()) as mock_file, \
                 patch('json.dump') as mock_json_dump:
                
                result_json_str = get_interactive_elements_main('test_session', output_file='test_elements.json')
                
                # Assertions
                assert json.loads(result_json_str) == expected_elements_data
                mock_json_dump.assert_called_once_with(expected_elements_data, mock_file.return_value, indent=2) # Use mock_file.return_value
                mock_file.assert_called_once_with('test_elements.json', 'w')
                
                # Check calls to build_naive_css_selector
                assert mock_build_selector.call_count == 3
                mock_build_selector.assert_any_call(mock_element1)
                mock_build_selector.assert_any_call(mock_element2)
                mock_build_selector.assert_any_call(mock_element3)

# Tests for collect_and_save_interactive_elements from src.playbookgen.utils.browser_helpers

def test_collect_and_save_no_elements():
    """Test collect_and_save_interactive_elements with no elements on the page."""
    mock_page = Mock()
    mock_page.query_selector_all.return_value = []
    
    with patch('builtins.open', mock_open()) as mock_file, \
         patch('json.dump') as mock_json_dump:
        
        collect_and_save_interactive_elements(mock_page, 'output_test.json')
        
        mock_json_dump.assert_called_once_with([], mock_file.return_value, indent=2) # Use mock_file.return_value
        mock_file.assert_called_once_with('output_test.json', 'w', encoding='utf-8') # Added encoding

def test_collect_and_save_with_various_elements():
    """Test collect_and_save with various mock elements and attributes."""
    mock_page = Mock()

    # Element 1: Link with ID, class, text
    mock_el1 = Mock()
    mock_el1.evaluate.return_value = "A" # Tag name
    mock_el1.inner_text.return_value = "Test Link"
    def el1_get_attribute(attr):
        if attr == "id": return "link-id"
        if attr == "class": return "link-class"
        if attr == "role": return "navigation"
        return None
    mock_el1.get_attribute.side_effect = el1_get_attribute
    mock_el1.bounding_box.return_value = {"x": 10, "y": 20, "width": 100, "height": 30}

    # Element 2: Input with type, placeholder, no class
    mock_el2 = Mock()
    mock_el2.evaluate.return_value = "INPUT" # Tag name
    mock_el2.inner_text.return_value = "" 
    def el2_get_attribute(attr):
        if attr == "id": return "input-id"
        if attr == "type": return "search"
        if attr == "placeholder": return "Search here..."
        return None
    mock_el2.get_attribute.side_effect = el2_get_attribute
    mock_el2.bounding_box.return_value = {"x": 50, "y": 60, "width": 200, "height": 40}

    # Element 3: Button with only a class and text
    mock_el3 = Mock()
    mock_el3.evaluate.return_value = "BUTTON" # Tag name
    mock_el3.inner_text.return_value = "Submit"
    def el3_get_attribute(attr):
        if attr == "class": return "btn-primary"
        return None
    mock_el3.get_attribute.side_effect = el3_get_attribute
    mock_el3.bounding_box.return_value = None # Test case where bounding_box might be None

    mock_page.query_selector_all.return_value = [mock_el1, mock_el2, mock_el3]

    expected_data = [
        {
            "index": 1, "tag": "A", "id": "link-id", "class": "link-class",
            "type": None, "role": "navigation", "text": "Test Link", "placeholder": None,
            "selector": "css=selector_for_el1",  # Added "css=" prefix
            "bounding_box": {"x": 10, "y": 20, "width": 100, "height": 30}
        },
        {
            "index": 2, "tag": "INPUT", "id": "input-id", "class": None,
            "type": "search", "role": None, "text": "", "placeholder": "Search here...",
            "selector": "css=selector_for_el2", # Added "css=" prefix
            "bounding_box": {"x": 50, "y": 60, "width": 200, "height": 40}
        },
        {
            "index": 3, "tag": "BUTTON", "id": None, "class": "btn-primary",
            "type": None, "role": None, "text": "Submit", "placeholder": None,
            "selector": "css=selector_for_el3", # Added "css=" prefix
            "bounding_box": None
        }
    ]

    # Patch build_naive_css_selector where it's looked up for collect_and_save_interactive_elements
    # which is src.playbookgen.utils.browser_helpers.build_naive_css_selector
    with patch('src.playbookgen.utils.browser_helpers.build_naive_css_selector') as mock_build_selector_collect:
        mock_build_selector_collect.side_effect = [
            "selector_for_el1", 
            "selector_for_el2", 
            "selector_for_el3"
        ]
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            collect_and_save_interactive_elements(mock_page, 'output_collect_test.json')
            
            mock_json_dump.assert_called_once_with(expected_data, mock_file.return_value, indent=2) # Use mock_file.return_value
            mock_file.assert_called_once_with('output_collect_test.json', 'w', encoding='utf-8') # Added encoding

            assert mock_build_selector_collect.call_count == 3
            mock_build_selector_collect.assert_any_call(mock_el1)
            mock_build_selector_collect.assert_any_call(mock_el2)
            mock_build_selector_collect.assert_any_call(mock_el3)

# Tests for do_browser_action from src.playbookgen.main
from src.playbookgen.main import do_browser_action

def test_do_browser_action_not_browser_type():
    """Test that do_browser_action does nothing if step type is not 'browser'."""
    mock_page = Mock()
    step = {"type": "not_browser", "cmd": "visit"}
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        do_browser_action(step)
        mock_page.goto.assert_not_called()
        mock_page.click.assert_not_called()
        mock_page.fill.assert_not_called()

def test_do_browser_action_session_not_exists():
    """Test that do_browser_action does nothing if the session doesn't exist (and not creating one)."""
    step = {"type": "browser", "cmd": "visit", "session": "non_existent_session"}
    with patch('src.playbookgen.main.browser_sessions', {}): # Ensure sessions dict is empty
        do_browser_action(step)
        # No page methods should be called on any mock page object

def test_do_browser_action_cmd_visit():
    """Test 'visit' command."""
    mock_page = Mock()
    step = {"type": "browser", "cmd": "visit", "url": "https://example.com", "session": "test_session"}
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        do_browser_action(step)
        mock_page.goto.assert_called_once_with("https://example.com")

def test_do_browser_action_cmd_click_with_selector():
    """Test 'click' command with a selector."""
    mock_page = Mock()
    step = {"type": "browser", "cmd": "click", "selector": "button#myBtn", "session": "test_session"}
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        do_browser_action(step)
        mock_page.click.assert_called_once_with("button#myBtn")

def test_do_browser_action_cmd_click_without_selector():
    """Test 'click' command without a selector."""
    mock_page = Mock()
    step = {"type": "browser", "cmd": "click", "session": "test_session"} # No selector
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        do_browser_action(step)
        mock_page.click.assert_not_called()

def test_do_browser_action_cmd_type_with_selector_and_text():
    """Test 'type' command with selector and text."""
    mock_page = Mock()
    step = {"type": "browser", "cmd": "type", "selector": "input#name", "text": "Hello", "session": "test_session"}
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        do_browser_action(step)
        mock_page.fill.assert_called_once_with("input#name", "Hello")

def test_do_browser_action_cmd_type_with_selector_no_text():
    """Test 'type' command with selector but no text (should type empty string)."""
    mock_page = Mock()
    step = {"type": "browser", "cmd": "type", "selector": "input#name", "session": "test_session"} # No text
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        do_browser_action(step)
        mock_page.fill.assert_called_once_with("input#name", "") # Default text is ""

def test_do_browser_action_cmd_type_without_selector():
    """Test 'type' command without a selector."""
    mock_page = Mock()
    step = {"type": "browser", "cmd": "type", "text": "Hello", "session": "test_session"} # No selector
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        do_browser_action(step)
        mock_page.fill.assert_not_called()

def test_do_browser_action_cmd_unknown():
    """Test an unknown command."""
    mock_page = Mock()
    step = {"type": "browser", "cmd": "unknown_cmd", "session": "test_session"}
    with patch('src.playbookgen.main.browser_sessions', {'test_session': mock_page}):
        with patch('builtins.print') as mock_print: # Mock print to check output
            do_browser_action(step)
            mock_page.goto.assert_not_called()
            mock_page.click.assert_not_called()
            mock_page.fill.assert_not_called()
            mock_print.assert_called_once_with("Unknown command:", "unknown_cmd")

def test_do_browser_action_creates_session():
    """Test the 'creates_session' logic."""
    mock_playwright_instance = Mock()
    mock_browser_instance = Mock()
    mock_new_page_instance = Mock()

    # Configure the mocks for the Playwright calls
    # sync_playwright().start() returns playwright_instance
    # playwright_instance.chromium.launch() returns browser_instance
    # browser_instance.new_page() returns new_page_instance
    
    # We need to mock the sync_playwright function itself which is imported in main.py
    # from playwright.sync_api import sync_playwright
    # So, the patch target is 'src.playbookgen.main.sync_playwright'
    
    with patch('src.playbookgen.main.sync_playwright') as mock_sync_playwright_func:
        # Configure the .start() method of the object returned by sync_playwright()
        mock_sync_playwright_func.return_value.start.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser_instance
        mock_browser_instance.new_page.return_value = mock_new_page_instance

        step_create_session = {
            "type": "browser", 
            "cmd": "visit", 
            "url": "https://newsession.com", 
            "creates_session": "my_new_session"
        }
        
        # Patch browser_sessions for this specific test, starting empty
        with patch('src.playbookgen.main.browser_sessions', {}) as mock_sessions_dict:
            do_browser_action(step_create_session)

            # Verify Playwright setup calls
            mock_sync_playwright_func.return_value.start.assert_called_once()
            mock_playwright_instance.chromium.launch.assert_called_once_with(headless=True)
            mock_browser_instance.new_page.assert_called_once()
            
            # Verify session was created and stored
            assert "my_new_session" in mock_sessions_dict
            assert mock_sessions_dict["my_new_session"] == mock_new_page_instance
            
            # Verify the initial command was executed on the new page
            mock_new_page_instance.goto.assert_called_once_with("https://newsession.com")

# Tests for add_playbook_step from src.playbookgen.main
from src.playbookgen.main import add_playbook_step, PlaybookState # Import PlaybookState for new_callable
import pytest # For checking exceptions

@patch('src.playbookgen.main.do_browser_action')
@patch('src.playbookgen.main.playbook_state', new_callable=lambda: PlaybookState()) # Use lambda for fresh instance
def test_add_playbook_step_sleep_valid(mock_state, mock_do_browser_action):
    """Test adding a valid 'sleep' step."""
    result_message = add_playbook_step(step_type="sleep", seconds=10)
    
    assert len(mock_state.commands) == 1
    expected_step = {"type": "sleep", "seconds": 10}
    assert mock_state.commands[0] == expected_step
    mock_do_browser_action.assert_not_called()
    assert "Added sleep step to the playbook" in result_message
    assert yaml.dump(expected_step, sort_keys=False) in result_message

def test_add_playbook_step_sleep_no_seconds():
    """Test 'sleep' step raises ValueError if seconds is not provided."""
    # Need to patch playbook_state here too, as the function modifies it before raising error potentially
    with patch('src.playbookgen.main.playbook_state', PlaybookState()):
        with pytest.raises(ValueError, match="The 'seconds' parameter must be provided for a sleep step."):
            add_playbook_step(step_type="sleep")

@patch('src.playbookgen.main.do_browser_action')
@patch('src.playbookgen.main.playbook_state', new_callable=lambda: PlaybookState())
def test_add_playbook_step_browser_visit(mock_state, mock_do_browser_action):
    """Test adding a 'browser' step for 'visit' command."""
    result_message = add_playbook_step(
        step_type="browser", 
        cmd="visit", 
        url="https://example.com", 
        session="s1",
        creates_session="s1_created" # Added to ensure all params are handled
    )
    
    expected_step = {
        "type": "browser", 
        "cmd": "visit", 
        "url": "https://example.com", 
        "session": "s1",
        "creates_session": "s1_created"
    }
    assert len(mock_state.commands) == 1
    assert mock_state.commands[0] == expected_step
    mock_do_browser_action.assert_called_once_with(expected_step)
    assert "Added step to the playbook" in result_message
    assert yaml.dump(expected_step, sort_keys=False) in result_message

# Tests for execute_tool_call from src.playbookgen.main
from src.playbookgen.main import execute_tool_call
from unittest.mock import MagicMock # Already imported Mock, but MagicMock is good for attribute access

def test_execute_tool_call_valid():
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "my_test_func"
    mock_tool_call.function.arguments = json.dumps({"arg1": "value1", "arg2": 123})

    mock_func = Mock(return_value="Function was called successfully")
    tools_map = {"my_test_func": mock_func}

    result = execute_tool_call(mock_tool_call, tools_map)

    mock_func.assert_called_once_with(arg1="value1", arg2=123)
    assert result == "Function was called successfully"

def test_execute_tool_call_unknown_function():
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "non_existent_func"
    mock_tool_call.function.arguments = json.dumps({})
    
    tools_map = {"some_other_func": Mock()}

    with pytest.raises(KeyError, match="non_existent_func"): # Check if the message contains the key
        execute_tool_call(mock_tool_call, tools_map)

def test_execute_tool_call_malformed_json_args():
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "my_test_func"
    mock_tool_call.function.arguments = "this is not valid json" # Malformed JSON

    mock_func = Mock()
    tools_map = {"my_test_func": mock_func}

    with pytest.raises(json.JSONDecodeError):
        execute_tool_call(mock_tool_call, tools_map)

def test_execute_tool_call_no_args():
    """Test a valid tool call to a function that expects no arguments."""
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "func_no_args"
    mock_tool_call.function.arguments = json.dumps({}) # Empty args

    mock_func = Mock(return_value="No-args function success")
    tools_map = {"func_no_args": mock_func}

    result = execute_tool_call(mock_tool_call, tools_map)

    mock_func.assert_called_once_with() # Expect call with no arguments
    assert result == "No-args function success"

def test_execute_tool_call_function_raises_exception():
    """Test that an exception raised by the called function propagates."""
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "failing_func"
    mock_tool_call.function.arguments = json.dumps({})

    mock_func = Mock(side_effect=ValueError("Something went wrong inside"))
    tools_map = {"failing_func": mock_func}

    with pytest.raises(ValueError, match="Something went wrong inside"):
        execute_tool_call(mock_tool_call, tools_map)

@patch('src.playbookgen.main.do_browser_action')
@patch('src.playbookgen.main.playbook_state', new_callable=lambda: PlaybookState())
def test_add_playbook_step_browser_click_with_selector(mock_state, mock_do_browser_action):
    """Test adding a 'browser' step for 'click' with selector."""
    result_message = add_playbook_step(
        step_type="browser", 
        cmd="click", 
        selector="#myButton", 
        session="s2"
    )
    
    expected_step = {
        "type": "browser", 
        "cmd": "click", 
        "selector": "#myButton", 
        "session": "s2"
    }
    assert len(mock_state.commands) == 1
    assert mock_state.commands[0] == expected_step
    mock_do_browser_action.assert_called_once_with(expected_step)
    assert "Added step to the playbook" in result_message

@patch('src.playbookgen.main.do_browser_action')
@patch('src.playbookgen.main.playbook_state', new_callable=lambda: PlaybookState())
def test_add_playbook_step_browser_type_with_text_and_selector(mock_state, mock_do_browser_action):
    """Test adding a 'browser' step for 'type' with text and selector."""
    result_message = add_playbook_step(
        step_type="browser", 
        cmd="type", 
        selector="input[name='q']", 
        text="search query", 
        session="s3"
    )
    
    expected_step = {
        "type": "browser", 
        "cmd": "type", 
        "selector": "input[name='q']", 
        "text": "search query", 
        "session": "s3"
    }
    assert len(mock_state.commands) == 1
    assert mock_state.commands[0] == expected_step
    mock_do_browser_action.assert_called_once_with(expected_step)
    assert "Added step to the playbook" in result_message

def test_add_playbook_step_browser_no_cmd():
    """Test 'browser' step raises ValueError if cmd is not provided."""
    with patch('src.playbookgen.main.playbook_state', PlaybookState()):
        with pytest.raises(ValueError, match="The 'cmd' parameter must be provided for a browser step."):
            add_playbook_step(step_type="browser", url="http://foo.com")

@patch('src.playbookgen.main.do_browser_action')
@patch('src.playbookgen.main.playbook_state', new_callable=lambda: PlaybookState())
def test_add_playbook_step_all_browser_params(mock_state, mock_do_browser_action):
    """Test adding a 'browser' step with all possible parameters."""
    step_details = {
        "cmd": "complex_action",
        "url": "https://complex.example.com",
        "selector": "div > .target",
        "text": "some complex text",
        "session": "session_complex",
        "creates_session": "new_session_complex"
    }
    result_message = add_playbook_step(step_type="browser", **step_details)
    
    expected_step = {"type": "browser", **step_details}
    assert len(mock_state.commands) == 1
    assert mock_state.commands[0] == expected_step
    mock_do_browser_action.assert_called_once_with(expected_step)
    assert "Added step to the playbook" in result_message
    assert yaml.dump(expected_step, sort_keys=False) in result_message

def test_build_naive_css_selector_tag_only():
    """Test that an element with no ID/class returns 'tag:nth-of-type(n)'."""
    mock_element = Mock()
    # Mock the result of the JavaScript evaluation
    mock_element.evaluate.return_value = "span:nth-of-type(3)"
    
    selector = build_naive_css_selector(mock_element)
    assert selector == "span:nth-of-type(3)"
    mock_element.evaluate.assert_called_once()
    args, _ = mock_element.evaluate.call_args
    js_function_str = args[0]
    assert "function getSelector(node)" in js_function_str

def test_build_naive_css_selector_nested_element():
    """Test a nested element selector string."""
    mock_element = Mock()
    # Mock the result of the JavaScript evaluation for a nested element
    mock_element.evaluate.return_value = "div.parent > span.child:nth-of-type(1)"
    
    selector = build_naive_css_selector(mock_element)
    assert selector == "div.parent > span.child:nth-of-type(1)"
    mock_element.evaluate.assert_called_once()
    args, _ = mock_element.evaluate.call_args
    js_function_str = args[0]
    assert "function getSelector(node)" in js_function_str
    
def test_build_naive_css_selector_root_element_html():
    """Test selector for the HTML element (should be just 'html')."""
    mock_element = Mock()
    mock_element.evaluate.return_value = "html" # JS should directly return 'html' for document.documentElement
    
    selector = build_naive_css_selector(mock_element)
    assert selector == "html"
    mock_element.evaluate.assert_called_once()
    args, _ = mock_element.evaluate.call_args
    js_function_str = args[0]
    assert "function getSelector(node)" in js_function_str

def test_build_naive_css_selector_root_element_body():
    """Test selector for the BODY element (should be just 'body')."""
    mock_element = Mock()
    mock_element.evaluate.return_value = "body" # JS should directly return 'body' for document.body
    
    selector = build_naive_css_selector(mock_element)
    assert selector == "body"
    mock_element.evaluate.assert_called_once()
    args, _ = mock_element.evaluate.call_args
    js_function_str = args[0]
    assert "function getSelector(node)" in js_function_str

def test_build_naive_css_selector_with_multiple_classes():
    """Test that an element with multiple classes uses the first one."""
    mock_element = Mock()
    # Mock the result of the JavaScript evaluation
    # The JS is expected to pick the first class: "class1"
    mock_element.evaluate.return_value = "p.class1:nth-of-type(1)" 
    
    selector = build_naive_css_selector(mock_element)
    assert selector == "p.class1:nth-of-type(1)"
    mock_element.evaluate.assert_called_once()
    args, _ = mock_element.evaluate.call_args
    js_function_str = args[0]
    assert "function getSelector(node)" in js_function_str
