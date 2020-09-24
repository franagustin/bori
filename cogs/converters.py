import dataclasses
import re
from typing import Dict, List, Set, Sequence, Tuple, Union

from discord.ext.commands import Context, Converter

from utils.message_utils import parse_args


DEFAULT_ADD_KWS = {
    'add', 'new', 'put', 'añadir', 'añade', 'agrega', 'agregar', 'nuevo', 'poner', 'pon'
}

DEFAULT_RM_KWS = {
    'remove', 'rm', 'quitar', 'quita', 'sacar', 'saca', 'eliminar', 'elimina'
}

DEFAULT_SET_KWS = {
    'set', 'only', 'establecer', 'establece', 'unico', 'único', 'solo', 'sólo'
}

DEFAULT_CHECK_KWS = {
    'check', 'list', 'view', 'chequear', 'chequea', 'listar', 'lista', 'ver', 've'
}

KwsType = Union[Tuple[str, ...], List[str], Set[str]]


@dataclasses.dataclass
class ActionConverter(Converter):
    add_kws: KwsType = dataclasses.field(default_factory=lambda: DEFAULT_ADD_KWS)
    rm_kws: KwsType = dataclasses.field(default_factory=lambda: DEFAULT_RM_KWS)
    set_kws: KwsType = dataclasses.field(default_factory=lambda: DEFAULT_SET_KWS)
    check_kws: KwsType = dataclasses.field(default_factory=lambda: DEFAULT_CHECK_KWS)
    allow_checks: bool = True
    default_action: str = None

    async def convert(self, _ctx: Context, action: str = None) -> Tuple[str, bool]:
        # pylint: disable=arguments-differ
        if self.allow_checks and (skip := action in self.check_kws):
            action = 'check'
        elif skip := action in self.add_kws:
            action = 'add'
        elif skip := action in self.rm_kws:
            action = 'remove'
        elif skip := action in self.set_kws:
            action = 'set'
        else:
            action = self.default_action
            skip = False
        return action, skip


@dataclasses.dataclass
class ESArgsConverter(ActionConverter):
    valid_args: Dict[str, bool] = dataclasses.field(default_factory=dict)
    aliases: Dict[str, str] = dataclasses.field(default_factory=dict)
    default_action: str = 'set'

    async def convert(self, _ctx: Context, args: str) -> Tuple[str, dict, List[str]]:
        # pylint: disable=arguments-differ
        split_args = args.split(' ')
        action, skip_first = await super().convert(split_args[0])
        if skip_first:
            split_args.pop(0)
        settings, bad_fields = self._parse_settings(action, split_args)
        return action, settings, bad_fields

    def _parse_settings(self, action: str, args: List[str]) -> Tuple[dict, List[str]]:
        settings, bad_fields = parse_args(args, self.valid_args)
        for alias, field in self.aliases.items():
            if alias in settings:
                new_value = settings.get(field, [])
                new_value.extend(settings[alias])
                settings[field] = new_value
                del settings[alias]
        bad_fields.extend([
            f for f, v in settings.items()
            if not isinstance(v, list) and action in ('add', 'remove')
        ])
        return settings, bad_fields


@dataclasses.dataclass
class SplitValueConverter(Converter):
    splitter_names: Sequence[str] = ('-s', '--splitter', 'splitter')
    splitters: Sequence[str] = (',', ';', '|')

    async def convert(self, _ctx: Context, unsplit_values: str) -> Tuple[str]:
        # pylint: disable=arguments-differ
        splitter = None
        for name in self.splitter_names:
            if match := re.search(f'(^{name} ?=? ?(.)) ?.*', unsplit_values):
                splitter = match.groups()[1]
                unsplit_values = unsplit_values.replace(match.groups()[0], '')
                split_values = unsplit_values.split(splitter)
        if splitter is None:
            for name in self.splitters:
                if len(split_values := unsplit_values.split(name)) > 1:
                    splitter = name
                    break
        return split_values
