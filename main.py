import os
import yaml
import ast
import redis
import time
import json
import subprocess
import datetime
from flask import Flask
from flask import request
app = Flask(__name__)


# {"hostname": {"curr":["remain","create_time","stop_time","update_time","charge","error"],"hist":["remain","create_time","stop_time","update_time","charge","error"]}}

r = redis.Redis(host='192.168.10.102', port=30273, password='FHv4uVkiqc')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        data = request.get_json()
        #r.delete(data["num"])
        secret = r.get(data["num"])
        print(data["num"])
        print(secret)
        pod_name = data["pod_name"]
        if secret is not None:
            secret = eval(secret.decode())
            remain = secret['curr']["remain"]
            if int(remain) > 0:
                # res = os.popen("curl --location --request GET 'http://127.0.0.1:30000/addgpu/namespace/default/pod/{}/gpu/1/isEntireMount/false'".format(pod_name)).read()
                # print("========={}===========".format(res))
                container = os.popen(
                    "docker container ls -a | grep  %s | grep entrypoint | grep Up " % (data["num"])).read()
                container = container.split(' ')[0]
                print(container)
                command = "docker commit %s" % ("%s %s" % (container,data["num"]))
                print(command)
                command = command.replace("\n", "")
                print(command)
                subprocess.check_output(command, shell=True, executable='/bin/bash')
                os.popen("kubectl apply -f /home/tiantian/{}/deploy.yaml".format(data["num"]))
                createtime = datetime.datetime.now()
                secret['curr']['status'] = "Running"
                secret['curr']['createTime'] = createtime
                secret['curr']['pod_name'] = pod_name
                print(secret)
                r.set(data["num"],str(secret))
                return "添加成功==剩余时长{}h==welcom==重新刷新一下哦".format(round(secret['curr']["remain"]/3600,2))
            else:
                return "余额不足======0w0"
        else:
            secret = data["secret"]
            curr = str({"curr" : {"remain":3600,"charge":[{"money": 0 ,"chargeTime":datetime.datetime.now()}]},"hist":{"list":[]}})
            r.set(data["num"],curr)
            return "创建新用户成功,请重新申请====owo"

@app.route('/remove', methods=['GET', 'POST'])
def remove():
    if request.method == 'POST':
        data = request.get_json()
        #r.delete(data["secret"])
        secret = r.get(data["num"])
        pod_name = data["pod_name"]
        # gpu_id = data["gpu_id"]
        if secret is not None:
            print(pod_name)
            # print(gpu_id)
            # res = os.popen("curl \
            #                 --location \
            #                 --request POST 'http://127.0.0.1:30000/removegpu/namespace/default/pod/{}/force/1' \
            #                 --header 'Content-Type: application/x-www-form-urlencoded' \
            #                 --data-urlencode 'uuids={}'".format(pod_name,gpu_id)).read()
            # print("======{}=======".format(res))
            container = os.popen(
                "docker container ls -a | grep  %s | grep entrypoint | grep Up" % (data["num"])).read()
            container = container.split(' ')[0]
            command = "docker commit %s" % ("%s %s" % (container, data["num"]))
            command = command.replace("\n", "")
            print(command)
            subprocess.check_output(command, shell=True, executable='/bin/bash')
            os.popen("kubectl apply -f /home/tiantian/{}/undeploy.yaml".format(data["num"]))
            secret = eval(secret.decode())
            createtime = secret['curr']['createTime']
            endtime = datetime.datetime.now()
            used = (endtime-createtime)
            print(used.seconds)
            remain = secret['curr']["remain"]
            secret['curr']['status'] = "end"
            secret['curr']["remain"] = int(remain) - int(used.seconds)
            secret['curr']['endTime'] = endtime
            hist = secret["hist"]["list"]
            if hist is not None:
                 hist.append({"createTime":createtime,"endTime":endtime})
            else:
                hist = [{"createTime":createtime,"endTime":endtime}]
            secret["hist"]["list"] = hist
            r.set(data["num"], str(secret))
            print(secret)

            return "移除成功==剩余时长{}h==请重新刷新一下".format(round(secret['curr']["remain"]/3600,2))
        else:
            return "未找到此用户========no"

@app.route('/charge', methods=['GET', 'POST'])
def charge():
    if request.method == 'POST':
        data = request.get_json()
        #r.delete(data["secret"])
        secret = r.get(data["num"])
        secret = eval(secret)
        charge = secret["curr"]["charge"]
        if charge is not None:
            charge.append({ "money": str(data["charge"]),"chargeTime": str(datetime.datetime.now())})
        else:
            charge = [{ "money": str(data["charge"]),"chargeTime": str(datetime.datetime.now())}]
        secret['curr']["charge"] = charge
        pre = secret['curr']['remain']
        remain = int(secret['curr']['remain']) + int(data["charge"]) * 3600
        secret['curr']['remain'] = remain
        r.set(data["num"], str(secret))
        print(secret)
        return "充值{}h==前{}s==后{}s=剩余{}h=".format(data["charge"],pre,remain,round(remain/3600,2))


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        data = request.get_json()
        os.system('kubectl delete pod {}'.format(data["pod_name"]))

        return "重置中，请重新刷新新密码登录owo"


@app.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = request.get_json()

        num = data["num"].split('code-server')[1]
        
        os.system('helm uninstall minio{}'.format(num))
        os.system('helm install minio{}   --set accessKey={},secretKey={} -f minio/values.yaml bitnami/minio'.format(num,data["user"],data["password"]))
       


        os.system('mc config host add {} http://192.168.10.102:3200{} {} {} --api=s3v4;'.format(data["num"],num,data["user"],data["password"]))
        

        os.system("mc mb {}{}".format(data["num"],data["buket"]))
        with open(r'/home/tiantian/{}/secret.yaml'.format(data["num"]),encoding="utf-8") as dataset:
            dataset = yaml.full_load(dataset)
            dataset["metadata"]["name"] = data["num"]
            dataset["stringData"]["aws.accessKeyId"] = data["user"]
            dataset["stringData"]["aws.secretKey"] = data["password"]

        with open(r'/home/tiantian/{}/secret.yaml'.format(data["num"]), 'w', encoding='utf-8') as f:

            yaml.dump(dataset, f, default_flow_style=False)


        with open(r'/home/tiantian/{}/dataset.yaml'.format(data["num"]),encoding="utf-8") as dataset:
            dataset = yaml.full_load(dataset)
            dataset["metadata"]["name"] = data["num"]
            dataset["metadata"]["mountPoint"] = "s3://{}/data".format(data["num"])
            dataset["spec"]["mounts"][0]["options"]["alluxio.underfs.s3.endpoint"] = "http://192.168.10.102:3200{}".format(num)
            dataset["spec"]["mounts"][0]["mountPoint"] = "s3://{}/data".format(data["num"])
            dataset["spec"]["mounts"][0]["name"] = data["num"]

        with open(r'/home/tiantian/{}/dataset.yaml'.format(data["num"]), 'w', encoding='utf-8') as f:

            yaml.dump(dataset, f, default_flow_style=False)


        with open(r'/home/tiantian/{}/runtime.yaml'.format(data["num"]),encoding="utf-8") as runtime:
            runtime = yaml.full_load(runtime)
            runtime["metadata"]["name"] = data["num"]

        with open(r'/home/tiantian/{}/runtime.yaml'.format(data["num"]), 'w', encoding='utf-8') as f:

            yaml.dump(runtime, f, default_flow_style=False)

        os.system("kubectl apply -f /home/tiantian/{}/dataset.yaml".format(data["num"]))
        os.system("kubectl apply -f /home/tiantian/{}/secret.yaml".format(data["num"]))
        os.system("kubectl apply -f /home/tiantian/{}/runtime.yaml".format(data["num"]))
        os.system("kubectl apply -f /home/tiantian/{}/deploy-data.yaml".format(data["num"]))
        return '正在努力挂载,请刷新后观察data目录'

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=29999, debug=True)


