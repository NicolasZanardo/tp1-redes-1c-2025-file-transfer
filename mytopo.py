from mininet.topo import Topo

class MyTopo(Topo):
    def __init__(self):
        Topo.__init__(self)
        
        # Agregar 3 switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        
        # Agregar 2 hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        
        # Conectar switches en cadena: s1 -- s2 -- s3
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        
        # Conectar h1 a s1 y h2 a s3
        self.addLink(h1, s1)
        self.addLink(h2, s3)

topos = {'mytopo': (lambda: MyTopo())}
