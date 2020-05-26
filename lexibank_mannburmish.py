import attr
from pathlib import Path
from csvw import Datatype

from pylexibank import Concept, Language, Cognate
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank.util import progressbar

from clldutils.misc import slug
from collections import defaultdict


@attr.s
class CustomConcept(Concept):
    Number = attr.ib(default=None)


@attr.s
class CustomCognate(Cognate):
    Segment_Slice = attr.ib(default=None)


@attr.s
class CustomLanguage(Language):
    Latitude = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    SubGroup = attr.ib(default="Burmish")
    Family = attr.ib(default="Sino-Tibetan")


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "mannburmish"
    language_class = CustomLanguage
    concept_class = CustomConcept
    cognate_class = CustomCognate

    def cmd_makecldf(self, args):
        args.writer.add_sources()

        # TODO: add concepts with `add_concepts`
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            idx = concept.id.split("-")[-1] + "_" + slug(concept.english)
            args.writer.add_concept(
                ID=idx,
                Name=concept.english,
                Number=concept.number,
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss,
            )
            concepts[concept.number] = idx
        languages = {}
        for language in self.languages:
            args.writer.add_language(**language)
            languages[language['Name']] = language['ID']

        data = self.raw_dir.read_csv(
                'Mann-redo.csv',
                delimiter='\t',
                dicts=True)

        words = defaultdict(list)
        for i, row in enumerate(data):
            for language, lid in languages.items():
                if row[language].strip():
                    number = row['Mann_number'][:-1]
                    words[lid, number] += [(row[language], row['Mann_number'],
                        str(i+1))]
        args.writer['FormTable', 'Segments'].separator = ' + '
        args.writer['FormTable', 'Segments'].datatype = Datatype.fromvalue(
                {'base': 'string', 'format': "([\\S]+)( [\\S]+)*"})

        for (language, number), values in words.items():
            value = ' '.join([x[0] for x in values])
            cogids = [x[1] for x in values]
            locids = '-'.join([x[2] for x in values])

            lexemes = args.writer.add_forms_from_value(
                    Language_ID=language,
                    Parameter_ID=concepts[str(int(number))],
                    Local_ID='{0}-{1}'.format(language, locids),
                    Value=value,
                    Source=['Mann1998']
                    )
            for lex in lexemes:
                for i, cogid in enumerate(cogids):
                    args.writer.add_cognate(
                            lexeme=lex,
                            Cognateset_ID=cogid,
                            Segment_Slice=i+1,
                            Source='Mann1998')

