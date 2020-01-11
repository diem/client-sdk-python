use std::io;
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr};
#[cfg(test)]
#[macro_use]
extern crate unwrap;

/// Details about an interface on this host
#[derive(Debug, PartialEq, Eq, Hash, Clone)]
pub struct Interface {
    /// The name of the interface.
    pub name: String,
    /// The address details of the interface.
    pub addr: IfAddr,
}

/// Details about the address of an interface on this host
#[derive(Debug, PartialEq, Eq, Hash, Clone)]
pub enum IfAddr {
    /// This is an Ipv4 interface.
    V4(Ifv4Addr),
    /// This is an Ipv6 interface.
    V6(Ifv6Addr),
}

/// Details about the ipv4 address of an interface on this host
#[derive(Debug, PartialEq, Eq, Hash, Clone)]
pub struct Ifv4Addr {
    /// The IP address of the interface.
    pub ip: Ipv4Addr,
    /// The netmask of the interface.
    pub netmask: Ipv4Addr,
    /// The broadcast address of the interface.
    pub broadcast: Option<Ipv4Addr>,
}

/// Details about the ipv6 address of an interface on this host
#[derive(Debug, PartialEq, Eq, Hash, Clone)]
pub struct Ifv6Addr {
    /// The IP address of the interface.
    pub ip: Ipv6Addr,
    /// The netmask of the interface.
    pub netmask: Ipv6Addr,
    /// The broadcast address of the interface.
    pub broadcast: Option<Ipv6Addr>,
}

impl Interface {
    /// Check whether this is a loopback interface.
    pub fn is_loopback(&self) -> bool {
        self.addr.is_loopback()
    }

    /// Get the IP address of this interface.
    pub fn ip(&self) -> IpAddr {
        self.addr.ip()
    }
}

impl IfAddr {
    /// Check whether this is a loopback address.
    pub fn is_loopback(&self) -> bool {
        match *self {
            IfAddr::V4(ref ifv4_addr) => ifv4_addr.is_loopback(),
            IfAddr::V6(ref ifv6_addr) => ifv6_addr.is_loopback(),
        }
    }

    /// Get the IP address of this interface address.
    pub fn ip(&self) -> IpAddr {
        match *self {
            IfAddr::V4(ref ifv4_addr) => IpAddr::V4(ifv4_addr.ip),
            IfAddr::V6(ref ifv6_addr) => IpAddr::V6(ifv6_addr.ip),
        }
    }
}

impl Ifv4Addr {
    /// Check whether this is a loopback address.
    pub fn is_loopback(&self) -> bool {
        self.ip.octets()[0] == 127
    }
}

impl Ifv6Addr {
    /// Check whether this is a loopback address.
    pub fn is_loopback(&self) -> bool {
        self.ip.segments() == [0, 0, 0, 0, 0, 0, 0, 1]
    }
}

pub fn get_if_addrs() -> io::Result<Vec<Interface>> {
    let mut ret = Vec::<Interface>::new();
    Ok(ret)
}
