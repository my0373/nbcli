# Examples

This file provides example commands for working with the local `nbcli` script and
the target NetBox API.

## Local script examples

Run the root script:

```
./nbcli status
```

Show CLI configuration:

```
./nbcli get cli config
```

Show available verbs or endpoints:

```
./nbcli show verbs
./nbcli show apps
./nbcli show endpoints
./nbcli show bgp
```

Select a single value from the CLI config:

```
./nbcli get cli config --path .timeout
```

List devices with filters:

```
./nbcli list dcim/devices --filter role=leaf --filter site=dc1
```

Output formats:

```
./nbcli get status --json
./nbcli get status --yaml
./nbcli get status --csv
```

Dump all objects to YAML:

```
./nbcli dump netbox_dump.yaml
```

## NetBox API examples

The commands below use endpoints discovered from `/api/` on your NetBox instance.

Get API status:

```
./nbcli get status
```

Dump the full API dataset:

```
./nbcli dump netbox_dump.yaml
```

Select a single value from a response:

```
./nbcli get status --path .netbox-version
./nbcli list dcim/devices --path .results.0.name
```

## Circuits objects

```
./nbcli list circuits/circuit-group-assignments
./nbcli list circuits/circuit-groups
./nbcli list circuits/circuit-terminations
./nbcli list circuits/circuit-types
./nbcli list circuits/circuits
./nbcli list circuits/provider-accounts
./nbcli list circuits/provider-networks
./nbcli list circuits/providers
./nbcli list circuits/virtual-circuit-terminations
./nbcli list circuits/virtual-circuit-types
./nbcli list circuits/virtual-circuits
```

## Core objects

```
./nbcli list core/background-queues
./nbcli list core/background-tasks
./nbcli list core/background-workers
./nbcli list core/data-files
./nbcli list core/data-sources
./nbcli list core/jobs
./nbcli list core/object-changes
./nbcli list core/object-types
```

## DCIM objects

```
./nbcli list dcim/cable-terminations
./nbcli list dcim/cables
./nbcli list dcim/connected-device
./nbcli list dcim/console-port-templates
./nbcli list dcim/console-ports
./nbcli list dcim/console-server-port-templates
./nbcli list dcim/console-server-ports
./nbcli list dcim/device-bay-templates
./nbcli list dcim/device-bays
./nbcli list dcim/device-roles
./nbcli list dcim/device-types
./nbcli list dcim/devices
./nbcli list dcim/front-port-templates
./nbcli list dcim/front-ports
./nbcli list dcim/interface-templates
./nbcli list dcim/interfaces
./nbcli list dcim/inventory-item-roles
./nbcli list dcim/inventory-item-templates
./nbcli list dcim/inventory-items
./nbcli list dcim/locations
./nbcli list dcim/mac-addresses
./nbcli list dcim/manufacturers
./nbcli list dcim/module-bay-templates
./nbcli list dcim/module-bays
./nbcli list dcim/module-type-profiles
./nbcli list dcim/module-types
./nbcli list dcim/modules
./nbcli list dcim/platforms
./nbcli list dcim/power-feeds
./nbcli list dcim/power-outlet-templates
./nbcli list dcim/power-outlets
./nbcli list dcim/power-panels
./nbcli list dcim/power-port-templates
./nbcli list dcim/power-ports
./nbcli list dcim/rack-reservations
./nbcli list dcim/rack-roles
./nbcli list dcim/rack-types
./nbcli list dcim/racks
./nbcli list dcim/rear-port-templates
./nbcli list dcim/rear-ports
./nbcli list dcim/regions
./nbcli list dcim/site-groups
./nbcli list dcim/sites
./nbcli list dcim/virtual-chassis
./nbcli list dcim/virtual-device-contexts
```

## Extras objects

```
./nbcli list extras/bookmarks
./nbcli list extras/config-context-profiles
./nbcli list extras/config-contexts
./nbcli list extras/config-templates
./nbcli list extras/custom-field-choice-sets
./nbcli list extras/custom-fields
./nbcli list extras/custom-links
./nbcli list extras/event-rules
./nbcli list extras/export-templates
./nbcli list extras/image-attachments
./nbcli list extras/journal-entries
./nbcli list extras/notification-groups
./nbcli list extras/notifications
./nbcli list extras/object-types
./nbcli list extras/saved-filters
./nbcli list extras/scripts
./nbcli list extras/subscriptions
./nbcli list extras/table-configs
./nbcli list extras/tagged-objects
./nbcli list extras/tags
./nbcli list extras/webhooks
```

## IPAM objects

```
./nbcli list ipam/aggregates
./nbcli list ipam/asn-ranges
./nbcli list ipam/asns
./nbcli list ipam/fhrp-group-assignments
./nbcli list ipam/fhrp-groups
./nbcli list ipam/ip-addresses
./nbcli list ipam/ip-ranges
./nbcli list ipam/prefixes
./nbcli list ipam/rirs
./nbcli list ipam/roles
./nbcli list ipam/route-targets
./nbcli list ipam/service-templates
./nbcli list ipam/services
./nbcli list ipam/vlan-groups
./nbcli list ipam/vlan-translation-policies
./nbcli list ipam/vlan-translation-rules
./nbcli list ipam/vlans
./nbcli list ipam/vrfs
```

## Plugins objects

```
./nbcli list plugins/bgp
./nbcli list plugins/branching
./nbcli list plugins/changes
./nbcli list plugins/custom-objects
./nbcli list plugins/diode
./nbcli list plugins/documents
./nbcli list plugins/floorplan
./nbcli list plugins/installed-plugins
./nbcli list plugins/lifecycle
./nbcli list plugins/netbox-dns
./nbcli list plugins/netbox_labs_console
./nbcli list plugins/netbox_topology_views
./nbcli list plugins/reorder
./nbcli list plugins/validity
```

## Tenancy objects

```
./nbcli list tenancy/contact-assignments
./nbcli list tenancy/contact-groups
./nbcli list tenancy/contact-roles
./nbcli list tenancy/contacts
./nbcli list tenancy/tenant-groups
./nbcli list tenancy/tenants
```

## Users objects

```
./nbcli list users/config
./nbcli list users/groups
./nbcli list users/permissions
./nbcli list users/tokens
./nbcli list users/users
```

## Virtualization objects

```
./nbcli list virtualization/cluster-groups
./nbcli list virtualization/cluster-types
./nbcli list virtualization/clusters
./nbcli list virtualization/interfaces
./nbcli list virtualization/virtual-disks
./nbcli list virtualization/virtual-machines
```

## VPN objects

```
./nbcli list vpn/ike-policies
./nbcli list vpn/ike-proposals
./nbcli list vpn/ipsec-policies
./nbcli list vpn/ipsec-profiles
./nbcli list vpn/ipsec-proposals
./nbcli list vpn/l2vpn-terminations
./nbcli list vpn/l2vpns
./nbcli list vpn/tunnel-groups
./nbcli list vpn/tunnel-terminations
./nbcli list vpn/tunnels
```

## Wireless objects

```
./nbcli list wireless/wireless-lan-groups
./nbcli list wireless/wireless-lans
./nbcli list wireless/wireless-links
```
