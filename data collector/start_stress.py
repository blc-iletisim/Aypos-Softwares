import requests as rq


def start_stress_es(number):

    vm_list = [
                # "aypostest11",
                "aypostest10",
                 "aypostest9",
                 "aypostest8",

                 # "aypostest7",

                # "ayposmedtest",
                  "aypostest4",
    ]

    vm_list = ["aypos_tester" + str(i) for i in range(number)]

    print(vm_list)

    for i in vm_list:

        try:

            stresc = rq.post("http://10.150.1.30:5001/stress", json=str({"vm": i}))
            print(stresc.json(), "success")

        except Exception as e:
            print("coulndt on:", i, e)


if __name__=="__main__":
    start_stress_es(10)
