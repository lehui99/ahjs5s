import json
import os
import subprocess
import sys
import time
import threading

import set_proxy

class Main(object):
    def __init__(self, config):
        self.config = config
    def load_config(self, config_path):
        with open(config_path) as config_file:
            return json.loads(config_file.read())
    def save_config(self, config_path, config):
        with open(config_path, 'w') as config_file:
            config_file.write(json.dumps(config))
    def start(self):
        try:
            prompt_input = raw_input
        except NameError:
            prompt_input = input
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        os.chdir('..')
        for i, prompt in enumerate(self.config['languages']):
            print("%d. %s" % (i + 1, prompt))
        language = int(prompt_input(self.config['select'])) - 1
        while True:
            for i, prompt in enumerate(self.config['translates']['menu_top'][language]):
                print("%d. %s" % (i + 1, prompt))
            sel = int(prompt_input(self.config['translates']['select'][language]))
            if sel == 1:
                if self.config['set_proxy']:
                    print(self.config['translates']['start_menu'][language][0] % ('127.0.0.1', self.config['http_proxy_port']))
                    set_proxy.set_proxy('http=127.0.0.1:%d' % (self.config['http_proxy_port'], ))
                else:
                    print(self.config['translates']['start_menu'][language][1] % ('127.0.0.1', self.config['http_proxy_port']))
                def start_main():
                    subprocess.call('3rd\\python\\python.exe main.py config.json > main.log 2>&1', shell=True)
                threading.Thread(target=start_main).start()
                main_config = self.load_config('config.json')
                def start_polipo(socks_proxy_port, http_proxy_port):
                    subprocess.call('3rd\\polipo\polipo.exe socksParentProxy=127.0.0.1:%d proxyPort=%d > polipo.log 2>&1' % (socks_proxy_port, http_proxy_port), shell=True)
                threading.Thread(target=start_polipo, args=(main_config['server_port'], self.config['http_proxy_port'])).start()
                if self.config['set_proxy']:
                    print("1. %s" % (self.config['translates']['start_menu'][language][2], ))
                    sel = int(prompt_input(self.config['translates']['select'][language]))
                    if sel == 1:
                        set_proxy.unset_proxy()
                print(self.config['translates']['start_menu'][language][3])
                while True:
                    time.sleep(3600)
            elif sel == 2:
                main_config = self.load_config('config.json')
                while True:
                    print("1. %s%d" % (self.config['translates']['edit_config_menu'][language][0], main_config['server_port']))
                    print("2. %s%d" % (self.config['translates']['edit_config_menu'][language][1], self.config['http_proxy_port']))
                    print("3. %s%s" % (self.config['translates']['edit_config_menu'][language][2], self.config['translates']['true_false'][language][0] if self.config['set_proxy'] else self.config['translates']['true_false'][language][1]))
                    print("0. %s" % (self.config['translates']['edit_config_menu'][language][3]))
                    sel = int(prompt_input(self.config['translates']['select'][language]))
                    if sel == 1:
                        main_config['server_port'] = int(prompt_input(self.config['translates']['edit_config_menu'][language][0]))
                        self.save_config('config.json', main_config)
                    elif sel == 2:
                        self.config['http_proxy_port'] = int(prompt_input(self.config['translates']['edit_config_menu'][language][1]))
                        self.save_config(os.path.join('windows', 'wizard.json'), self.config)
                    elif sel == 3:
                        for i, prompt in enumerate(self.config['translates']['true_false'][language]):
                            print("%d. %s" % (i + 1, prompt))
                        sel = int(prompt_input(self.config['translates']['select'][language][0]))
                        if sel == 1:
                            self.config['set_proxy'] = True
                        elif sel == 2:
                            self.config['set_proxy'] = False
                        self.save_config(os.path.join('windows', 'wizard.json'), self.config)
                    elif sel == 0:
                        break

def main(json_path):
    with open(json_path) as json_file:
        config = json.loads(json_file.read())
    Main(config).start()

if __name__ == '__main__':
    main(sys.argv[1])
