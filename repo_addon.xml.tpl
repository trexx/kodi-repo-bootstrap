<?xml version="1.0" encoding="UTF-8"?>
<addon id="{addonid}" name="{name}" version="{version}" provider-name="{author}">
    <requires>
        <import addon="xbmc.addon" version="12.0.0"/>
    </requires>
    <extension point="xbmc.addon.repository" name="{name}">
        <dir>
            <info compressed="false">{url}/addons.xml</info>
            <checksum>{url}/addons.xml.md5</checksum>
            <datadir zip="true">{url}/</datadir>
            <hashes>false</hashes>
        </dir>
    </extension>
    <extension point="xbmc.addon.metadata">
        <summary>{summary}</summary>
        <description>{description}</description>
        <platform>all</platform>
    </extension>
</addon>
