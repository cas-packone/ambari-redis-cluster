import os,base64,socket
from time import sleep
from resource_management import *

class RedisMaster(Script):
    
    def install(self, env):
        #update ruby
        import params;
        env.set_params(params) 
        self.install_packages(env)        
        service_packagedir = params.service_packagedir
        Execute('find '+params.service_packagedir+' -iname "*.sh" | xargs chmod +x')
        cmd = format("{service_packagedir}/scripts/upgrade_ruby.sh")
        Execute(cmd)        
               

    def configure(self, env):       
        import params;
        port = params.port
        db_path_master=  params.db_path + '/data/' + str(params.port)
        port_replica = params.port + 1
        db_path_replica = params.db_path + '/data/' + str(port_replica)
        log_path = params.db_path + '/log/'
        #dir 
        if not os.path.exists(db_path_master):
            cmd = format('mkdir -p {db_path_master}')        
            Execute(cmd)
        if not os.path.exists(db_path_replica):        
            cmd = format('mkdir -p {db_path_replica}')        
            Execute(cmd)
        if not os.path.exists(log_path):        
            cmd = format('mkdir -p {log_path}')       
            Execute(cmd)
        
        #conf file 
        conf_path=params.conf_path
        cmd = format('mkdir -p {conf_path}')       
        Execute(cmd)
        
        #port        
        params.redis_port=port
        env.set_params(params)
        server_cnf_content = InlineTemplate(params.server_cnf_content)   
        File(format("{conf_path}/{port}.cnf"), content=server_cnf_content)
        
        #port_replica
        params.redis_port=port_replica
        env.set_params(params)
        server_cnf_content = InlineTemplate(params.server_cnf_content)   
        File(format("{conf_path}/{port_replica}.cnf"), content=server_cnf_content)
                
        

    def start(self, env):
        import params;
        self.configure(env)
        conf_path = params.conf_path
        ports = [params.port,params.port+1]
        for index_p,p in enumerate(ports,start=0):                                        
            cmd =format('redis-server {conf_path}/{p}.cnf')
            Execute(cmd)
            
        for index_p,p in enumerate(ports,start=0):
            cmd=format('redis-cli -c -p {p} <<EOF CONFIG SET protected-mode no \n EOF')
            Execute(cmd)
            
        if params.redis_current_host == params.redis_hosts[0]:
            sleep(10)
            cluster_service =''
            for index_h,h in enumerate(params.redis_hosts,start=0):
                ip=socket.gethostbyname(h)
                for index_p,p in enumerate(ports,start=0):                  
                   cluster_service = cluster_service + ip + ":" + str(p) + " "
            params.cluster_service = cluster_service
            env.set_params(params)  
            service_packagedir = params.service_packagedir
            cluster_path = service_packagedir + '/scripts/init_cluster.sh'
            File(cluster_path,
             content=Template("init_cluster.sh.j2"),
             mode=0777
            )
            cmd = format("{service_packagedir}/scripts/init_cluster.sh")
            Execute('echo "Running ' + cmd + '" as root')
            Execute(cmd,ignore_failures=True)            

    def stop(self, env):
        import params;
        ports = [params.port,params.port+1]
        for index_p,p in enumerate(ports,start=0):                                        
            pid_file = '/var/run/redis-' + str(p) + '.pid'
            print 'pid_file:' + pid_file            
            cmd =format('cat {pid_file} | xargs kill -9 ')
            try:
               Execute(cmd,logoutput=True)
            except:
               print 'can not find pid process,skip this'

    def restart(self, env):
        self.stop(env)
        self.start(env)

    def status(self, env):
        print "checking status..."
        #import params;
        #port = params.port
        port =7000
        pid_file= format('/var/run/redis-{port}.pid')     
        check_process_status(pid_file)
        #import params                    
        #ports = [params.port,params.port+1]
        #for index_p,p in enumerate(ports,start=0):                   
        #    pid_file = '/var/run/redis-' + str(p) + '.pid'               
        #    check_process_status(pid_file)
    

if __name__ == "__main__":
    RedisMaster().execute()
