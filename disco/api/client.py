import six
import json

from disco.api.http import Routes, HTTPClient
from disco.util.logging import LoggingClass

from disco.types.user import User
from disco.types.message import Message
from disco.types.guild import Guild, GuildMember, GuildBan, Role, GuildEmoji
from disco.types.channel import Channel
from disco.types.invite import Invite
from disco.types.webhook import Webhook


def optional(**kwargs):
    """
    Takes a set of keyword arguments, creating a dictionary with only the non-
    null values.

    :returns: dict
    """
    return {k: v for k, v in six.iteritems(kwargs) if v is not None}


class APIClient(LoggingClass):
    """
    An abstraction over a :class:`disco.api.http.HTTPClient`, which composes
    requests from provided data, and fits models with the returned data. The APIClient
    is the only path to the API used within models/other interfaces, and it's
    the recommended path for all third-party users/implementations.

    Args
    ----
    token : str
        The Discord authentication token (without prefixes) to be used for all
        HTTP requests.
    client : Optional[:class:`disco.client.Client`]
        The Disco client this APIClient is a member of. This is used when constructing
        and fitting models from response data.

    Attributes
    ----------
    client : Optional[:class:`disco.client.Client`]
        The Disco client this APIClient is a member of.
    http : :class:`disco.http.HTTPClient`
        The HTTPClient this APIClient uses for all requests.
    """
    def __init__(self, token, client=None):
        super(APIClient, self).__init__()

        self.client = client
        self.http = HTTPClient(token)

    def gateway_get(self):
        data = self.http(Routes.GATEWAY_GET).json()
        return data

    def gateway_bot_get(self):
        data = self.http(Routes.GATEWAY_BOT_GET).json()
        return data

    def channels_get(self, channel):
        r = self.http(Routes.CHANNELS_GET, dict(channel=channel))
        return Channel.create(self.client, r.json())

    def channels_modify(self, channel, **kwargs):
        r = self.http(Routes.CHANNELS_MODIFY, dict(channel=channel), json=kwargs)
        return Channel.create(self.client, r.json())

    def channels_delete(self, channel):
        r = self.http(Routes.CHANNELS_DELETE, dict(channel=channel))
        return Channel.create(self.client, r.json())

    def channels_typing(self, channel):
        self.http(Routes.CHANNELS_TYPING, dict(channel=channel))

    def channels_messages_list(self, channel, around=None, before=None, after=None, limit=50):
        r = self.http(Routes.CHANNELS_MESSAGES_LIST, dict(channel=channel), params=optional(
            around=around,
            before=before,
            after=after,
            limit=limit
        ))

        return Message.create_map(self.client, r.json())

    def channels_messages_get(self, channel, message):
        r = self.http(Routes.CHANNELS_MESSAGES_GET, dict(channel=channel, message=message))
        return Message.create(self.client, r.json())

    def channels_messages_create(self, channel, content=None, nonce=None, tts=False, attachment=None, embed=None):
        payload = {
            'nonce': nonce,
            'tts': tts,
        }

        if content:
            payload['content'] = content

        if embed:
            payload['embed'] = embed.to_dict()

        if attachment:
            r = self.http(Routes.CHANNELS_MESSAGES_CREATE, dict(channel=channel), data={'payload_json': json.dumps(payload)}, files={
                'file': (attachment[0], attachment[1])
            })
        else:
            r = self.http(Routes.CHANNELS_MESSAGES_CREATE, dict(channel=channel), json=payload)

        return Message.create(self.client, r.json())

    def channels_messages_modify(self, channel, message, content, embed=None):
        payload = {
            'content': content,
        }

        if embed:
            payload['embed'] = embed.to_dict()

        r = self.http(Routes.CHANNELS_MESSAGES_MODIFY,
                      dict(channel=channel, message=message),
                      json=payload)
        return Message.create(self.client, r.json())

    def channels_messages_delete(self, channel, message):
        self.http(Routes.CHANNELS_MESSAGES_DELETE, dict(channel=channel, message=message))

    def channels_messages_delete_bulk(self, channel, messages):
        self.http(Routes.CHANNELS_MESSAGES_DELETE_BULK, dict(channel=channel), json={'messages': messages})

    def channels_messages_reactions_get(self, channel, message, emoji):
        r = self.http(Routes.CHANNELS_MESSAGES_REACTIONS_GET, dict(channel=channel, message=message, emoji=emoji))
        return User.create_map(self.client, r.json())

    def channels_messages_reactions_create(self, channel, message, emoji):
        self.http(Routes.CHANNELS_MESSAGES_REACTIONS_CREATE, dict(channel=channel, message=message, emoji=emoji))

    def channels_messages_reactions_delete(self, channel, message, emoji, user=None):
        route = Routes.CHANNELS_MESSAGES_REACTIONS_DELETE_ME
        obj = dict(channel=channel, message=message, emoji=emoji)

        if user:
            route = Routes.CHANNELS_MESSAGES_REACTIONS_DELETE_USER
            obj['user'] = user

        self.http(route, obj)

    def channels_permissions_modify(self, channel, permission, allow, deny, typ):
        self.http(Routes.CHANNELS_PERMISSIONS_MODIFY, dict(channel=channel, permission=permission), json={
            'allow': allow,
            'deny': deny,
            'type': typ,
        })

    def channels_permissions_delete(self, channel, permission):
        self.http(Routes.CHANNELS_PERMISSIONS_DELETE, dict(channel=channel, permission=permission))

    def channels_invites_list(self, channel):
        r = self.http(Routes.CHANNELS_INVITES_LIST, dict(channel=channel))
        return Invite.create_map(self.client, r.json())

    def channels_invites_create(self, channel, max_age=86400, max_uses=0, temporary=False, unique=False):
        r = self.http(Routes.CHANNELS_INVITES_CREATE, dict(channel=channel), json={
            'max_age': max_age,
            'max_uses': max_uses,
            'temporary': temporary,
            'unique': unique
        })
        return Invite.create(self.client, r.json())

    def channels_pins_list(self, channel):
        r = self.http(Routes.CHANNELS_PINS_LIST, dict(channel=channel))
        return Message.create_map(self.client, r.json())

    def channels_pins_create(self, channel, message):
        self.http(Routes.CHANNELS_PINS_CREATE, dict(channel=channel, message=message))

    def channels_pins_delete(self, channel, message):
        self.http(Routes.CHANNELS_PINS_DELETE, dict(channel=channel, message=message))

    def channels_webhooks_create(self, channel, name=None, avatar=None):
        r = self.http(Routes.CHANNELS_WEBHOOKS_CREATE, dict(channel=channel), json=optional(
            name=name,
            avatar=avatar,
        ))
        return Webhook.create(self.client, r.json())

    def channels_webhooks_list(self, channel):
        r = self.http(Routes.CHANNELS_WEBHOOKS_LIST, dict(channel=channel))
        return Webhook.create_map(self.client, r.json())

    def guilds_get(self, guild):
        r = self.http(Routes.GUILDS_GET, dict(guild=guild))
        return Guild.create(self.client, r.json())

    def guilds_modify(self, guild, **kwargs):
        r = self.http(Routes.GUILDS_MODIFY, dict(guild=guild), json=kwargs)
        return Guild.create(self.client, r.json())

    def guilds_delete(self, guild):
        r = self.http(Routes.GUILDS_DELETE, dict(guild=guild))
        return Guild.create(self.client, r.json())

    def guilds_channels_list(self, guild):
        r = self.http(Routes.GUILDS_CHANNELS_LIST, dict(guild=guild))
        return Channel.create_hash(self.client, 'id', r.json(), guild_id=guild)

    def guilds_channels_create(self, guild, name, channel_type, bitrate=None, user_limit=None, permission_overwrites=[]):
        payload = {
            'name': name,
            'channel_type': channel_type,
            'permission_overwrites': [i.to_dict() for i in permission_overwrites],
        }

        if channel_type == 'text':
            pass
        elif channel_type == 'voice':
            if bitrate is not None:
                payload['bitrate'] = bitrate

            if user_limit is not None:
                payload['user_limit'] = user_limit
        else:
            # TODO: better error here?
            raise Exception('Invalid channel type: {}'.format(channel_type))

        r = self.http(Routes.GUILDS_CHANNELS_CREATE, dict(guild=guild), json=payload)
        return Channel.create(self.client, r.json(), guild_id=guild)

    def guilds_channels_modify(self, guild, channel, position):
        self.http(Routes.GUILDS_CHANNELS_MODIFY, dict(guild=guild), json={
            'id': channel,
            'position': position,
        })

    def guilds_members_list(self, guild):
        r = self.http(Routes.GUILDS_MEMBERS_LIST, dict(guild=guild))
        return GuildMember.create_hash(self.client, 'id', r.json(), guild_id=guild)

    def guilds_members_get(self, guild, member):
        r = self.http(Routes.GUILDS_MEMBERS_GET, dict(guild=guild, member=member))
        return GuildMember.create(self.client, r.json(), guild_id=guild)

    def guilds_members_modify(self, guild, member, **kwargs):
        self.http(Routes.GUILDS_MEMBERS_MODIFY, dict(guild=guild, member=member), json=optional(**kwargs))

    def guilds_members_roles_add(self, guild, member, role):
        self.http(Routes.GUILDS_MEMBERS_ROLES_ADD, dict(guild=guild, member=member, role=role))

    def guilds_members_roles_remove(self, guild, member, role):
        self.http(Routes.GUILDS_MEMBERS_ROLES_REMOVE, dict(guild=guild, member=member, role=role))

    def guilds_members_me_nick(self, guild, nick):
        self.http(Routes.GUILDS_MEMBERS_ME_NICK, dict(guild=guild), json={'nick': nick})

    def guilds_members_kick(self, guild, member):
        self.http(Routes.GUILDS_MEMBERS_KICK, dict(guild=guild, member=member))

    def guilds_bans_list(self, guild):
        r = self.http(Routes.GUILDS_BANS_LIST, dict(guild=guild))
        return GuildBan.create_hash(self.client, 'user.id', r.json())

    def guilds_bans_create(self, guild, user, delete_message_days):
        self.http(Routes.GUILDS_BANS_CREATE, dict(guild=guild, user=user), params={
            'delete-message-days': delete_message_days,
        })

    def guilds_bans_delete(self, guild, user):
        self.http(Routes.GUILDS_BANS_DELETE, dict(guild=guild, user=user))

    def guilds_roles_list(self, guild):
        r = self.http(Routes.GUILDS_ROLES_LIST, dict(guild=guild))
        return Role.create_map(self.client, r.json(), guild_id=guild)

    def guilds_roles_create(self, guild):
        r = self.http(Routes.GUILDS_ROLES_CREATE, dict(guild=guild))
        return Role.create(self.client, r.json(), guild_id=guild)

    def guilds_roles_modify_batch(self, guild, roles):
        r = self.http(Routes.GUILDS_ROLES_MODIFY_BATCH, dict(guild=guild), json=roles)
        return Role.create_map(self.client, r.json(), guild_id=guild)

    def guilds_roles_modify(self, guild, role, **kwargs):
        r = self.http(Routes.GUILDS_ROLES_MODIFY, dict(guild=guild, role=role), json=kwargs)
        return Role.create(self.client, r.json(), guild_id=guild)

    def guilds_roles_delete(self, guild, role):
        self.http(Routes.GUILDS_ROLES_DELETE, dict(guild=guild, role=role))

    def guilds_webhooks_list(self, guild):
        r = self.http(Routes.GUILDS_WEBHOOKS_LIST, dict(guild=guild))
        return Webhook.create_map(self.client, r.json())

    def guilds_emojis_list(self, guild):
        r = self.http(Routes.GUILDS_EMOJIS_LIST, dict(guild=guild))
        return GuildEmoji.create_map(self.client, r.json())

    def guilds_emojis_create(self, guild, **kwargs):
        r = self.http(Routes.GUILDS_EMOJIS_CREATE, dict(guild=guild), json=kwargs)
        return GuildEmoji.create(self.client, r.json())

    def guilds_emojis_modify(self, guild, emoji, **kwargs):
        r = self.http(Routes.GUILDS_EMOJIS_MODIFY, dict(guild=guild, emoji=emoji), json=kwargs)
        return GuildEmoji.create(self.client, r.json())

    def guilds_emojis_delete(self, guild, emoji):
        self.http(Routes.GUILDS_EMOJIS_DELETE, dict(guild=guild, emoji=emoji))

    def users_me_get(self):
        return User.create(self.client, self.http(Routes.USERS_ME_GET).json())

    def users_me_patch(self, payload):
        r = self.http(Routes.USERS_ME_PATCH, json=payload)
        return User.create(self.client, r.json())

    def users_me_guilds_delete(self, guild):
        self.http(Routes.USERS_ME_GUILDS_DELETE, dict(guild=guild))

    def users_me_dms_create(self, recipient_id):
        r = self.http(Routes.USERS_ME_DMS_CREATE, json={
            'recipient_id': recipient_id,
        })
        return Channel.create(self.client, r.json())

    def invites_get(self, invite):
        r = self.http(Routes.INVITES_GET, dict(invite=invite))
        return Invite.create(self.client, r.json())

    def invites_delete(self, invite):
        r = self.http(Routes.INVITES_DELETE, dict(invite=invite))
        return Invite.create(self.client, r.json())

    def webhooks_get(self, webhook):
        r = self.http(Routes.WEBHOOKS_GET, dict(webhook=webhook))
        return Webhook.create(self.client, r.json())

    def webhooks_modify(self, webhook, name=None, avatar=None):
        r = self.http(Routes.WEBHOOKS_MODIFY, dict(webhook=webhook), json=optional(
            name=name,
            avatar=avatar,
        ))
        return Webhook.create(self.client, r.json())

    def webhooks_delete(self, webhook):
        self.http(Routes.WEBHOOKS_DELETE, dict(webhook=webhook))

    def webhooks_token_get(self, webhook, token):
        r = self.http(Routes.WEBHOOKS_TOKEN_GET, dict(webhook=webhook, token=token))
        return Webhook.create(self.client, r.json())

    def webhooks_token_modify(self, webhook, token, name=None, avatar=None):
        r = self.http(Routes.WEBHOOKS_TOKEN_MODIFY, dict(webhook=webhook, token=token), json=optional(
            name=name,
            avatar=avatar,
        ))
        return Webhook.create(self.client, r.json())

    def webhooks_token_delete(self, webhook, token):
        self.http(Routes.WEBHOOKS_TOKEN_DELETE, dict(webhook=webhook, token=token))

    def webhooks_token_execute(self, webhook, token, data, wait=False):
        obj = self.http(
            Routes.WEBHOOKS_TOKEN_EXECUTE,
            dict(webhook=webhook, token=token),
            json=optional(**data), params={'wait': int(wait)})

        if wait:
            return Message.create(self.client, obj.json())
