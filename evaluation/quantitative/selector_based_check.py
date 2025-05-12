import yaml

base_selectors = []

"""
This method compares selector usage in manually created vs. LLM-generated YAML files to verify if 
the LLM's commands cover all necessary actions. The manual YAML serves as the gold standard, 
meaning all its commands should be replicated by the LLM.
"""

def get_base_selectors(file_path):
    with open(file_path, 'r') as file:
        content = yaml.safe_load(file)
    
    for key, value in content.items():
        if key == "commands":
            for v in value:
                for k,c in v.items():
                    if k == "selector":
                        base_selectors.append(c)
                    
def read_and_loop_yaml(file_path):
    tmp_base_selector = base_selectors.copy()
    tmp_not_in_base_selector = []
    len_base_selectors = len(base_selectors)
    # Open and read the YAML file
    with open(file_path, 'r') as file:
        content = yaml.safe_load(file)
    
    # Loop through the YAML content
    print(f"File: {file_path}")
    for key, value in content.items():
        if key == "commands":
            for v in value:
                for k,c in v.items():
                    if k == "cmd":
                        None
                    elif k == "selector":
                        if c in tmp_base_selector:
                            tmp_base_selector.remove(c)
                        else:
                            tmp_not_in_base_selector.append(c)
    print(f"Base selector list length: {len_base_selectors}")
    print(f"Tmp selector list length: {len(tmp_base_selector)}")
    similarity_in_selectors = ((len_base_selectors - len(tmp_base_selector)) / len_base_selectors) * 100
    print(f"The similarity in used selectors: {similarity_in_selectors:.2f}%")
    print(f"Used selectors, that are not in the base: {tmp_not_in_base_selector}")
    print("-"*50)


print("\nGives a harsh similarity check for the used selectors")
print("-"*50)

# It uses the manual playbook as the base
file_path = "../playbooks/manual/admin1.yml"
get_base_selectors(file_path)
read_and_loop_yaml(file_path)

file_path = "../playbooks/llm/admin1_a.yml"
read_and_loop_yaml(file_path)
