import yaml


"""
This method uses scoring to determine if all the necessary steps are taken during the tests.
First the scores should be defined manually. An issue that also arises from this evaluation method, is that
all the selectors has to be defined before-hand and it cannot evaluate if unseen actions were used in the playbook.
"""

# This can be given for commands and for selectors separately, here are just a few examples:
high_prio_cmds = ["visit"] # 10pts
mid_prio_cmds = ["type"] # 5pts
low_prio_cmds = ["click"] # 2pts

high_prio_selectors = ["input[name='username']", "input[name='password']"] # 4pts
mid_prio_selectors = ["button[type='submit'][value='Apply']","a[href='?view=watch&mid=1']"] # 2pts
low_prio_selectors = ["button[name='action'][value='logout']"] # 1pts

def read_and_loop_yaml(file_path):
    overall_score = 0
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
                        overall_score += 10 if c in high_prio_cmds else 0
                        overall_score += 5 if c in mid_prio_cmds else 0
                        overall_score += 2 if c in low_prio_cmds else 0
                    elif k == "selector":
                        overall_score += 4 if c in high_prio_selectors else 0
                        overall_score += 2 if c in mid_prio_selectors else 0
                        overall_score += 1 if c in low_prio_selectors else 0

    print(f"The overall score: {overall_score}")
    print("-"*50)


print("\nRegarding the overall score, the higher the better.")
print("-"*50)

file_path = "../playbooks/manual/admin1.yml"
read_and_loop_yaml(file_path)

file_path = "../playbooks/llm/admin1_a.yml"
read_and_loop_yaml(file_path)
