# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# Panadería POS — despliegue en tres máquinas virtuales (Fase 2, sección 1).
#
#   dns-vm    192.168.56.10   BIND9, zona panaderia-pos.test
#   back-vm   192.168.56.12   api.panaderia-pos.test  (Nginx gateway + 3 microservicios)
#   front-vm  192.168.56.11   panaderia-pos.test      (Nginx + HTML/CSS/JS)
#
# Uso, desde la carpeta del proyecto:
#   vagrant up                 crea y configura las tres máquinas
#   vagrant provision back-vm  vuelve a desplegar el back-end después de cambiar el código
#   vagrant halt               apaga las máquinas
#
# La caja bento/ubuntu-22.04 existe para Intel/AMD y para Apple Silicon (M1):
# Vagrant descarga sola la versión que corresponde a cada computador.
# Se usa el provisionador "ansible_local": Ansible se instala y corre DENTRO de
# cada máquina, así no hace falta instalar Ansible en Windows ni en Mac.

MACHINES = [
  { name: "dns-vm",   hostname: "ns",  ip: "192.168.56.10", memory: 768 },
  { name: "back-vm",  hostname: "api", ip: "192.168.56.12", memory: 1024 },
  { name: "front-vm", hostname: "www", ip: "192.168.56.11", memory: 768 },
]

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04"

  # En Windows con WSL2/Hyper-V activo VirtualBox arranca más lento: se da más tiempo.
  config.vm.boot_timeout = 600

  # La carpeta del proyecto queda disponible en /vagrant dentro de cada máquina.
  config.vm.synced_folder ".", "/vagrant"

  MACHINES.each do |machine|
    config.vm.define machine[:name] do |node|
      node.vm.hostname = machine[:hostname]
      node.vm.network "private_network", ip: machine[:ip]

      node.vm.provider "virtualbox" do |vb|
        vb.name = "panaderia-#{machine[:name]}"
        vb.memory = machine[:memory]
        vb.cpus = 1
        # Evita el error "failed to create /dev/null" de VirtualBox en Windows.
        vb.customize ["modifyvm", :id, "--uart1", "off"]
      end

      node.vm.provision "ansible_local" do |ansible|
        ansible.provisioning_path = "/vagrant/ansible"
        ansible.playbook = "site.yml"
        ansible.install_mode = "pip"
      end
    end
  end
end
