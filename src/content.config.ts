import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const temiCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/temi' }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    description: z.string(),
    categoria: z.enum([
      'economia-lavoro',
      'servizi-pubblici',
      'territorio-ambiente',
      'governance-finanze',
      'cultura-societa'
    ]),
    priorita: z.number().default(10),
    isPilotDeepDive: z.boolean().default(false),
    lastUpdated: z.string(),
    commissione: z.string().optional(),
    keywords: z.array(z.string()).default([]),
    kpis: z.array(z.object({
      label: z.string(),
      value: z.string(),
      trend: z.enum(['up', 'down', 'stable']),
      trendValue: z.string().optional()
    })).default([]),
    charts: z.array(z.object({
      id: z.string(),
      type: z.enum(['line', 'bar', 'donut', 'area']),
      title: z.string(),
      data: z.object({
        labels: z.array(z.string()),
        datasets: z.array(z.object({
          label: z.string(),
          values: z.array(z.number()),
          color: z.string()
        }))
      }),
      source: z.string()
    })).default([]),
    fonti: z.array(z.object({
      nome: z.string(),
      url: z.string(),
      tipo: z.string()
    })).default([]),
    correlati: z.array(z.string()).default([])
  })
});

const fontiCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/fonti' }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    description: z.string(),
    url: z.string(),
    tipo: z.enum(['istituzionale', 'ricerca', 'opendata', 'media', 'associazione']),
    categorie: z.array(z.string()).default([]),
    dataFormats: z.array(z.string()).default([]),
    frequenzaAggiornamento: z.string().default('Variabile')
  })
});

const tesiCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/tesi' }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    status: z.enum(['placeholder', 'draft', 'published']).default('placeholder'),
    macroArea: z.string().optional(),
    description: z.string().optional(),
    pdfFile: z.string().optional(),
    lastUpdated: z.string()
  })
});

export const collections = {
  temi: temiCollection,
  fonti: fontiCollection,
  tesi: tesiCollection
};
