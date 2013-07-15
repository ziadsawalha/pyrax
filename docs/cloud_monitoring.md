# Cloud Monitoring

## Basic Concepts
Rackspace Cloud Monitoring provides timely and accurate information about how your resources are performing. It supplies you with key information that can help you manage your business by enabling you to keep track of your cloud resources and receive instant notification when a resource needs your attention. You can quickly create multiple monitors with predefined checks, such as PING, HTTPS, SMTP, and many others.

## Monitoring in pyrax
Once you have authenticated, you can reference the monitoring service via `pyrax.cloud_monitoring`. This object is the client through which you interact with Cloud Monitoring.

For the sake of brevity and convenience, it is common to define abbreviated aliases for the modules. All the code in the document assumes that at the top of your script, you have added the following line:

    cm = pyrax.cloud_monitoring


## Key Terminology
### Entity
In Rackspace Cloud Monitoring, an entity is the object or resource that you want to monitor. It can be any object or device that you want to monitor. It's commonly a web server, but it might also be a website, a web page or a web service.

When you create an entity, you'll specify characteristics that describe what you are monitoring. At a minimum you must specify a name for the entity. The name is a user-friendly label or description that helps you identify the resource. You can also specify other attributes of the entity, such the entity's IP address, and any meta data that you'd like to associate with the entity.

### Check
Once you've created an entity, you can configure one or more checks for it. A check is the foundational building block of the monitoring system, and is always associated with an entity. The check specifies the parts or pieces of the entity that you want to monitor, the monitoring frequency, how many monitoring zones are launching the check, and so on. Basically it contains the specific details of how you are monitoring the entity.

You can associate one or more checks with an entity. An entity must have at least one check, but by creating multiple checks for an entity, you can monitor several different aspects of a single resource.

For each check you create within the monitoring system, you'll designate a check type. The check type tells the monitoring system which method to use, PING, HTTP, SMTP, and so on, when investigating the monitored resource. Rackspace Cloud Monitoring check types are fully described here.

Note that if something happens to your resource, the check does not trigger a notification action. Instead, notifications are triggered by alarms that you create separately and associate with the check.

### Monitoring Zones
When you create a check, you specify which monitoring zone(s) you want to launch the check from. A monitoring zone is the point of origin or "launch point" of the check. This concept of a monitoring zone is similar to that of a datacenter, however in the monitoring system, you can think of it more as a geographical region.

You can launch checks for a particular entity from multiple monitoring zones. This allows you to observe the performance of an entity from different regions of the world. It is also a way to prevent false alarms. For example, if the check from one monitoring zone reports that an entity is down, a second or third monitoring zone might report that the entity is up and running. This gives you a better picture of an entity's overall health.

### Collectors
A collector collects data from the monitoring zone and is mapped directly to an individual machine or a virtual machine. Monitoring zones contain many collectors, all of which will be within the IP address range listed in the response. Note that there may also be unallocated IP addresses or unrelated machines within that IP address range.

### Monitoring Agent
Note: The Monitoring Agent is a Preview feature.

The agent provides insight into the internals of your servers with checks for information such as load average and network usage. The agent runs as a single small service that runs scheduled checks and pushes metrics to the rest of Cloud Monitoring so the metrics can be analyzed, alerted on, and archived. These metrics are gathered via checks using agent check types, and can be used with the other Cloud Monitoring primatives such as alarms. See Section B.2, “Agent Check Types” for a list of agent check types.

### Alarms
An alarm contains a set of rules that determine when the monitoring system sends a notification. You can create multiple alarms for the different checks types associated with an entity. For example, if your entity is a web server that hosts your company's website, you can create one alarm to monitor the server itself, and another alarm to monitor the website.

The alarms language provides you with scoping parameters that let you pinpoint the value that will trigger the alarm. The scoping parameters are inherently flexible, so that you can set up multiple checks to trigger a single alarm. The alarm language supplies an adaptable triggering system that makes it easy for you to define different formulas for each alarm that monitors an entity's uptime. To learn how to use the alarm language to create robust monitors, see Alert Triggering and Alarms.

### Notifications
A notification is an informational message that you receive from the monitoring system when an alarm is triggered. You can set up notifications to alert a single individual or an entire team. Rackspace Cloud Monitoring currently supports webhooks and email for sending notifications.

### Notification Plans
A notification plan contains a set of notification rules to execute when an alarm is triggered. A notification plan can contain multiple notifications for each of the following states:

* Critical
* Warning
* Ok


## How Cloud Monitoring Works
Cloud Monitoring helps you keep a keen eye on all of your resources, from web sites to web servers, routers, load balancers, and more. Here is an overview of the Monitoring workflow:

* You create an entity to represent the item you want to monitor. For example, the entity might represent a web site.
* You attach a predefined check to the entity. For example, you could use the PING check to monitor your web site's public IP address.
* You can run your checks from multiple monitoring zones to provide redundant monitoring as well as voting logic to avoid false alarms.
* You create a notification which lets you define an action which Cloud Monitoring uses to communicate with you when a problem occurs. For example, you might define a notification that specifies an email that Cloud Monitoring will send when a condition is met.
* You create notification plans allow you to organize a set of several notifications, or actions, that are taken for different severities.
* You define one or more alarms for each check. An alarm lets you specify trigger conditions for the various metrics returned by the check. When a specific condition is met, the alarm is triggered and your notification plan is put into action. For example, your alarm may indicate a PING response time. If this time elapses, the alarm could send you an email or a webhook to a URL.

## Working with Cloud Monitoring in Pyrax
OK, now that the terminology has been defined, we can put this to work. We begin by creating an `entity`:

