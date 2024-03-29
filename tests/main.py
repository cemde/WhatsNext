from time import sleep
import sys
import os
sys.path.append(os.path.realpath("."))

import whatsnext as wn


def train_model(artifact: str, resource: str, learning_rate: float, num_hidden: int = 5):
    print(f"Artifacts:     {artifact}")
    print(f"resource:      {resource}")
    print(f"learning_rate: {learning_rate}")
    print(f"num_hidden:    {num_hidden}")
    n_secs = 10
    print(f"Sleeping for   {n_secs} seconds")
    sleep(n_secs)


# Connect to server
server = wn.Server("127.0.0.1", 8808)


####### Projects on server
# add project
server.append_project("Test Project", "This is a test project")
server.append_project("project_name", "This is a test project 2")
# get project
project = server.get_project("project_name")
# delete project
server.delete_project("project_name")

######## Handle jobs in project
project.append_queue(wn.Job("sailing-abroad-1", "train", parameters={"a": 1, "b": 1}))
project.append_queue(wn.Job("sailing-abroad-2", "train", parameters={"a": 1, "b": 2}))
# project.pop_queue()
# project.clear_queue()
# project.get_queue()
# project.set_description("This is a test project 3") set_title

client = wn.Client("usernamee", "ClusterA", "", project)
resource = client.allocate_resource(cpu=-1, accelerator=[0,1])

while resource.active():
    job = project.fetch_job()
    job.run()

print("A")
