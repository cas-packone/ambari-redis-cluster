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
        Execute('cd '+params.service_packagedir+'; find -iname "*.sh" | xargs chmod +x')
        cmd = format("{service_packagedir}/scripts/upgrade_ruby.sh; rm -rf {db_path}/data/*")
        Execute(cmd)

    def configure(self, env):       
        import params;
        port = params.port
        db_path_master=  params.db_path + '/data/' + str(params.port)
        port_replica = params.port_replica
        db_path_replica = params.db_path + '/data/' + str(port_replica)
        #dir 
        if not os.path.exists(db_path_master):
            cmd = format('mkdir -p {db_path_master}')        
            Execute(cmd)
        if not os.path.exists(db_path_replica):        
            cmd = format('mkdir -p {db_path_replica}')        
            Execute(cmd)

    def start(self, env):
        import params
        db_path = params.db_path
        self.configure(env)
        ports = [params.port,params.port_replica]
        for index_p,p in enumerate(ports,start=0):                                        
            cmd =format('echo "redis-server --port {p} --cluster-enabled yes --cluster-config-file nodes-{p}.conf --cluster-node-timeout 5000 --appendonly yes --daemonize yes --pidfile {db_path}/redis-{p}.pid --dir {db_path}/data/{p} --dbfilename dump-{p}.rdb --appendfilename appendonly-{p}.aof --logfile {db_path}/redis-{p}.log"|at now')
            Execute(cmd)
            
        sleep(5)
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

        password=params.password
        if password.strip():
            sleep(30) #waiting for cluster initialized
            for index_p,p in enumerate(ports,start=0):
                cmd=format('redis-cli -c -p {p} <<EOF CONFIG SET requirepass {password} \n EOF')
                Execute(cmd)

    def stop(self, env):
        import params
        db_path = params.db_path
        ports = [params.port,params.port_replica]
        for index_p,p in enumerate(ports,start=0):                                        
            pid_file = format('{db_path}/redis-{p}.pid')
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
        import status_params
        env.set_params(status_params)
        pid_file= format('{db_path}/redis-{port}.pid')     
        check_process_status(pid_file)
        #ports = [params.port,params.port+1]
        #for index_p,p in enumerate(ports,start=0):                   
        #    pid_file = '/var/run/redis-' + str(p) + '.pid'               
        #    check_process_status(pid_file)
     

if __name__ == "__main__":
    RedisMaster().execute()
